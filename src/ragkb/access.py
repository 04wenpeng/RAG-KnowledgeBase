# -*- coding: utf-8 -*-
"""访问控制：给局域网/外网访问加一道口令，同时保证本机永远免密且是管理员。

设计取舍：
  · 本机（127.0.0.1 / ::1）永远直接放行 —— 你自己用不该被打断；
  · 其它机器必须先用口令换一个签名 token（cookie），有效期默认 7 天；
  · 危险操作（改 API 配置、重建索引、导入/删除资料）只允许本机做，
    外人即使有口令也只能问答、看历史、上传文件。
  · 口令和签名密钥都存在 config/access.json，随时可改、可关。

token 是无状态的：`过期时间.签名`，签名 = HMAC-SHA256(secret, 过期时间)。
重启服务不用清会话表。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from pathlib import Path

from .config import BASE_DIR

ACCESS_FILE = BASE_DIR / "config" / "access.json"
COOKIE_NAME = "rag_kb"
_LOCK = threading.RLock()

DEFAULTS = {
    "enabled": True,
    "password": "",          # 明文口令，仅存本机；空则由 config() 生成
    "secret": "",            # token 签名密钥
    "ttl_days": 7,
}


def _load() -> dict:
    if not ACCESS_FILE.exists():
        return {}
    try:
        data = json.loads(ACCESS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(cfg: dict) -> None:
    ACCESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = ACCESS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ACCESS_FILE)


def config() -> dict:
    """读配置；缺密码/密钥就补上（首次运行自动生成口令并打印）。"""
    with _LOCK:
        cfg = dict(DEFAULTS)
        cfg.update(_load())
        changed = False
        if not cfg.get("secret"):
            cfg["secret"] = secrets.token_hex(16)
            changed = True
        if not cfg.get("password"):
            cfg["password"] = "kb-" + secrets.token_hex(3)
            changed = True
            print(f"\n  🔑 已生成访问口令：{cfg['password']}")
            print(f"     （存在 {ACCESS_FILE}，可随时改）\n")
        if changed:
            _save(cfg)
        return cfg


def enabled() -> bool:
    return bool(config().get("enabled", True))


def set_password(password: str) -> dict:
    with _LOCK:
        cfg = config()
        cfg["password"] = password
        _save(cfg)
        return cfg


def set_enabled(flag: bool) -> dict:
    with _LOCK:
        cfg = config()
        cfg["enabled"] = bool(flag)
        _save(cfg)
        return cfg


# ———————————————— token ————————————————
def _sign(secret: str, msg: str) -> str:
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def issue_token() -> str:
    cfg = config()
    days = int(cfg.get("ttl_days") or 7)
    exp = int(time.time()) + days * 86400
    msg = str(exp)
    return f"{msg}.{_sign(cfg['secret'], msg)}"


def token_ok(token: str) -> bool:
    if not token or "." not in token:
        return False
    exp_s, sig = token.rsplit(".", 1)
    try:
        exp = int(exp_s)
    except ValueError:
        return False
    if exp < int(time.time()):
        return False
    cfg = config()
    return hmac.compare_digest(sig, _sign(cfg["secret"], exp_s))


def verify_password(password: str) -> bool:
    cfg = config()
    return bool(password) and hmac.compare_digest(str(password), str(cfg.get("password") or ""))


# ———————————————— 防暴力破解 ————————————————
# 同一 IP 在 10 分钟内错 5 次，就锁 60 秒。
# 60 秒很短（人手误输不难受），但把爆破速度压到 5 次/分钟：
# 16^6 ≈ 1677 万种组合，按这个速度要试十几年。
MAX_FAILS = 5
FAIL_WINDOW = 600
LOCK_SECONDS = 60
_FAILS: dict[str, list[float]] = {}
_FAIL_LOCK = threading.Lock()


def login_blocked(ip: str) -> tuple[bool, int]:
    """返回 (是否被锁, 还需等待秒数)。"""
    now = time.time()
    with _FAIL_LOCK:
        shots = [t for t in _FAILS.get(ip, []) if now - t < FAIL_WINDOW]
        _FAILS[ip] = shots
        if len(shots) >= MAX_FAILS:
            wait = int(LOCK_SECONDS - (now - shots[-1]))
            if wait > 0:
                return True, wait
            _FAILS[ip] = []          # 锁到期，重新开始计数
    return False, 0


def record_failure(ip: str) -> None:
    with _FAIL_LOCK:
        _FAILS.setdefault(ip, []).append(time.time())


def clear_failures(ip: str) -> None:
    with _FAIL_LOCK:
        _FAILS.pop(ip, None)


# ———————————————— 授权策略 ————————————————
# 策略：问答模块完全公开（不输口令就能用）；管理功能才要口令。
#   公开：问答页 / 资料库页（只读）/ 提问 / 检索 / 统计 / 文件列表 / 对话历史
#   管理：改配置、重建索引、导入外部目录、上传、删除资料（需口令；本机免密）
PUBLIC_APIS = {
    ("GET", "api/whoami"),
    ("GET", "api/stats"),
    ("GET", "api/files"),
    ("GET", "api/library"),
    ("GET", "api/preview"),
    ("GET", "api/chats"),
    ("GET", "api/selftest_result"),
    ("POST", "api/ask"),
    ("POST", "api/search"),
    ("POST", "api/chats"),
    ("POST", "api/selftest_result"),
}
PUBLIC_PAGES = {"/", "/index.html", "/library", "/login", "/logout"}


def is_public(method: str, path: str) -> bool:
    clean = path.rstrip("/") or "/"
    if method == "GET" and clean in PUBLIC_PAGES:
        return True
    stripped = clean.lstrip("/")
    # 对话历史：列 / 读单个 / 追加消息，都算问答模块的一部分
    if method == "GET" and (stripped == "api/chats" or stripped.startswith("api/chats/")):
        return True
    if method == "POST" and (stripped == "api/chats" or stripped.endswith("/messages")):
        return True
    return (method, stripped) in PUBLIC_APIS


def is_admin_path(method: str, path: str) -> bool:
    return not is_public(method, path)


def allow(method: str, path: str, *, is_local: bool, token: str | None) -> bool:
    """总闸：True 放行。"""
    if not enabled():
        return True
    if is_public(method, path):
        return True          # 问答模块：谁都能用，不要口令
    if is_local:
        return True          # 本机做管理免密
    return token_ok(token or "")   # 远程做管理必须输口令


def snapshot() -> dict:
    """给管理界面看的当前状态（含口令明文：只有管理员能读到）。"""
    cfg = config()
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "password": cfg.get("password", ""),
        "ttl_days": int(cfg.get("ttl_days") or 7),
    }


def update(payload: dict) -> dict:
    """改口令 / 有效期 / 开关。改了口令就轮换密钥，旧 token 立刻失效。"""
    with _LOCK:
        cfg = config()
        rotated = False
        new_pw = (payload.get("password") or "").strip()
        if new_pw and new_pw != cfg.get("password"):
            cfg["password"] = new_pw
            cfg["secret"] = secrets.token_hex(16)
            rotated = True
        if payload.get("ttl_days") is not None:
            try:
                cfg["ttl_days"] = max(1, min(90, int(payload["ttl_days"])))
            except (TypeError, ValueError):
                pass
        if payload.get("enabled") is not None:
            cfg["enabled"] = bool(payload["enabled"])
        _save(cfg)
        return {"enabled": cfg["enabled"], "password": cfg["password"],
                "ttl_days": cfg["ttl_days"], "secret_rotated": rotated}
