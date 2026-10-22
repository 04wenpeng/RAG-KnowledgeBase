# -*- coding: utf-8 -*-
"""大模型 API 配置档案（多套配置的增删改查 + 启用 + 连通性测试）。

存盘位置：config/llm_profiles.json
对外提供：
    list_profiles() / get_profile() / create_profile() / update_profile()
    delete_profile() / activate_profile() / test_profile()
    active_llm_config()   -> (base_url, api_key, model) 或 None
    active_embedding()    -> ("offline"|"dashscope"|"ollama", model, key)
"""
from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR

PROFILE_DIR = BASE_DIR / "config"
PROFILE_FILE = PROFILE_DIR / "llm_profiles.json"

_LOCK = threading.RLock()

# 服务商预设：选服务商后前端自动带出地址和模型
PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek 官方",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "needs_key": True,
        "hint": "只提供对话模型，没有 embedding 接口；嵌入建议用「离线」或「百炼」",
    },
    "dashscope": {
        "label": "阿里云百炼",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "needs_key": True,
        "hint": "对话 + 嵌入一体，有免费额度；可同时用作嵌入模型来源",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "needs_key": True,
        "hint": "需要能访问 api.openai.com 的网络环境",
    },
    "ollama": {
        "label": "本地 Ollama",
        "base_url": "http://localhost:11434/v1",
        "model": "qwen3:4b",
        "needs_key": False,
        "hint": "本机需先安装 Ollama 并 ollama pull 模型",
    },
    "custom": {
        "label": "自定义（OpenAI 兼容）",
        "base_url": "",
        "model": "",
        "needs_key": True,
        "hint": "任何兼容 /chat/completions 的服务，填完整 base_url（含 /v1）",
    },
}

EMBEDDING_MODES = {
    "offline": "离线哈希向量（无需 Key，词面相似）",
    "dashscope": "阿里云百炼 text-embedding（语义级，需 Key）",
    "ollama": "本地 Ollama 嵌入模型",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _empty_store() -> dict:
    return {"version": 1, "active_id": "", "profiles": []}


def _read() -> dict:
    if not PROFILE_FILE.exists():
        return _empty_store()
    try:
        data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _empty_store()
    data.setdefault("version", 1)
    data.setdefault("active_id", "")
    data.setdefault("profiles", [])
    return data


def _write(data: dict) -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = PROFILE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PROFILE_FILE)


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 10:
        return "*" * len(key)
    return f"{key[:5]}****{key[-4:]}"


# —————————————————————— 查询 ——————————————————————
def list_profiles(mask: bool = True) -> list[dict]:
    with _LOCK:
        data = _read()
        active = data.get("active_id", "")
        out = []
        for p in data["profiles"]:
            item = dict(p)
            item["active"] = p.get("id") == active
            if mask:
                item["api_key_masked"] = mask_key(p.get("api_key", ""))
                item["api_key"] = ""
                item["has_key"] = bool(p.get("api_key"))
                item["embedding_api_key_masked"] = mask_key(p.get("embedding_api_key", ""))
                item["embedding_api_key"] = ""
            out.append(item)
        return out


def get_profile(pid: str) -> dict | None:
    with _LOCK:
        for p in _read()["profiles"]:
            if p.get("id") == pid:
                return dict(p)
    return None


def active_profile() -> dict | None:
    with _LOCK:
        data = _read()
        active = data.get("active_id", "")
        for p in data["profiles"]:
            if p.get("id") == active:
                return dict(p)
    return None


# —————————————————————— 增 / 改 / 删 ——————————————————————
def _clean_payload(payload: dict, existing: dict | None = None) -> dict:
    existing = existing or {}
    provider = (payload.get("provider") or existing.get("provider") or "custom").strip()
    preset = PROVIDERS.get(provider, PROVIDERS["custom"])

    def pick(field, default=""):
        val = payload.get(field)
        if val is None or str(val).strip() == "":
            return existing.get(field, default) or default
        return str(val).strip()

    embedding = pick("embedding", "offline")
    if embedding not in EMBEDDING_MODES:
        embedding = "offline"

    return {
        "name": pick("name", preset["label"]),
        "provider": provider,
        "base_url": pick("base_url", preset["base_url"]).rstrip("/"),
        "model": pick("model", preset["model"]),
        "api_key": pick("api_key"),
        "embedding": embedding,
        "embedding_model": pick("embedding_model", "text-embedding-v1" if embedding == "dashscope" else ""),
        "embedding_api_key": pick("embedding_api_key"),
    }


def create_profile(payload: dict) -> dict:
    with _LOCK:
        data = _read()
        fields = _clean_payload(payload)
        profile = {
            "id": "p_" + uuid.uuid4().hex[:8],
            **fields,
            "created_at": _now(),
            "updated_at": _now(),
            "last_test": {},
        }
        data["profiles"].append(profile)
        # 第一个配置自动启用
        if not data.get("active_id"):
            data["active_id"] = profile["id"]
        _write(data)
        return profile


def update_profile(pid: str, payload: dict) -> dict | None:
    with _LOCK:
        data = _read()
        for i, p in enumerate(data["profiles"]):
            if p.get("id") != pid:
                continue
            fields = _clean_payload(payload, existing=p)
            p.update(fields)
            p["updated_at"] = _now()
            data["profiles"][i] = p
            _write(data)
            return p
    return None


def delete_profile(pid: str) -> bool:
    with _LOCK:
        data = _read()
        before = len(data["profiles"])
        data["profiles"] = [p for p in data["profiles"] if p.get("id") != pid]
        if len(data["profiles"]) == before:
            return False
        if data.get("active_id") == pid:
            data["active_id"] = data["profiles"][0]["id"] if data["profiles"] else ""
        _write(data)
        return True


def activate_profile(pid: str) -> bool:
    with _LOCK:
        data = _read()
        if not any(p.get("id") == pid for p in data["profiles"]):
            return False
        data["active_id"] = pid
        _write(data)
        return True


# —————————————————————— 解析成实际调用参数 ——————————————————————
def active_llm_config():
    """当前启用的对话模型配置 -> (base_url, api_key, model)；没配则 None。"""
    p = active_profile()
    if not p:
        return None
    base_url = (p.get("base_url") or "").strip()
    model = (p.get("model") or "").strip()
    if not base_url or not model:
        return None
    provider = p.get("provider")
    key = (p.get("api_key") or "").strip()
    if p.get("provider") == "ollama" or not PROVIDERS.get(provider, {}).get("needs_key", True):
        return (base_url, key, model)
    if not key:
        return None
    return (base_url, key, model)


def active_embedding():
    """当前启用的嵌入方案 -> (mode, model, api_key)。"""
    p = active_profile()
    if not p:
        return ("offline", "", "")
    mode = p.get("embedding") or "offline"
    key = (p.get("embedding_api_key") or "").strip()
    if not key and p.get("provider") == "dashscope":
        key = (p.get("api_key") or "").strip()
    return (mode, (p.get("embedding_model") or "").strip(), key)


# —————————————————————— 连通性测试 ——————————————————————
def test_profile(pid: str, timeout: int = 25) -> dict:
    """真的发一次最小请求，返回 {ok, status, message, latency}。"""
    p = get_profile(pid)
    if not p:
        return {"ok": False, "status": 0, "message": "配置不存在"}

    base_url = (p.get("base_url") or "").strip().rstrip("/")
    model = (p.get("model") or "").strip()
    key = (p.get("api_key") or "").strip()
    provider = p.get("provider") or "custom"

    if not base_url or not model:
        return {"ok": False, "status": 0, "message": "Base URL 或模型名为空"}

    url = base_url + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "只回复两个字：可用"}],
        "max_tokens": 16,
        "temperature": 0,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    t0 = time.time()
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        reply = ""
        try:
            reply = body["choices"][0]["message"]["content"].strip()[:60]
        except Exception:
            reply = "(返回结构不是标准 chat/completions)"
        result = {
            "ok": True,
            "status": 200,
            "message": f"调用成功，模型回复：{reply}",
            "latency": round(time.time() - t0, 2),
            "at": _now(),
        }
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")
        except Exception:
            pass
        hints = {
            401: "Key 无效或已失效，重新复制一次（注意别带空格换行）",
            402: "账户余额不足，需要先充值",
            403: "Key 无权访问该模型，或账号未开通",
            404: "模型名或地址不对，检查 Base URL（含 /v1）和模型名",
            429: "限流或额度用尽，稍后再试",
        }
        result = {
            "ok": False,
            "status": exc.code,
            "message": hints.get(exc.code, "调用失败") + (f"｜{detail[:200]}" if detail else ""),
            "latency": round(time.time() - t0, 2),
            "at": _now(),
        }
    except Exception as exc:
        result = {
            "ok": False,
            "status": 0,
            "message": f"连接失败：{type(exc).__name__}: {exc}",
            "latency": round(time.time() - t0, 2),
            "at": _now(),
        }

    with _LOCK:
        data = _read()
        for i, item in enumerate(data["profiles"]):
            if item.get("id") == pid:
                data["profiles"][i]["last_test"] = result
                _write(data)
                break
    return result


def ensure_default_profile() -> None:
    """首次启动时，如果 .env 里有可用 Key，自动生成一条配置，免得空白。"""
    import os

    with _LOCK:
        data = _read()
        if data["profiles"]:
            return
    candidates = [
        ("dashscope", os.getenv("DASHSCOPE_API_KEY", "")),
        ("deepseek", os.getenv("DEEPSEEK_API_KEY", "")),
        ("openai", os.getenv("OPENAI_API_KEY", "")),
    ]
    for provider, key in candidates:
        if key:
            preset = PROVIDERS[provider]
            create_profile(
                {
                    "name": preset["label"] + "（来自 .env）",
                    "provider": provider,
                    "base_url": preset["base_url"],
                    "model": preset["model"],
                    "api_key": key,
                    "embedding": "dashscope" if provider == "dashscope" else "offline",
                    "embedding_model": "text-embedding-v1" if provider == "dashscope" else "",
                }
            )
            return
