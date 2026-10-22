# -*- coding: utf-8 -*-
"""按需启动 Ollama：知识库启动时如果当前配置是本地模型，才把 Ollama 拉起来。

不再需要开机自启。判断逻辑：
    当前启用的档案 provider == "ollama"  且  11434 端口没人监听  →  启动 serve
其它情况什么都不做（用 DeepSeek 时完全不碰 Ollama）。

用法：
    .venv\\Scripts\\python.exe src\\tools\\ensure_ollama.py          # 需要才启动
    .venv\\Scripts\\python.exe src\\tools\\ensure_ollama.py --force  # 不管配置，强制启动
    .venv\\Scripts\\python.exe src\\tools\\ensure_ollama.py --stop    # 停止
    .venv\\Scripts\\python.exe src\\tools\\ensure_ollama.py --status
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # src/
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

OLLAMA_EXE = PROJECT / "ollama" / "app" / "ollama.exe"
OLLAMA_APP = PROJECT / "ollama" / "app" / "ollama app.exe"
HOST, PORT = "127.0.0.1", 11434
LOG = PROJECT / "ollama" / "serve.log"


def listening() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, PORT)) == 0


def healthy() -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/api/tags", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def active_provider() -> str:
    try:
        from ragkb.profiles import active_profile

        prof = active_profile() or {}
        return (prof.get("provider") or "").lower()
    except Exception:
        return ""


def start(force: bool = False) -> int:
    provider = active_provider()
    if not force and provider != "ollama":
        print(f"[跳过] 当前启用的是「{provider or '未配置'}」，不需要本地模型")
        return 0
    if listening() and healthy():
        print(f"[已在运行] Ollama 127.0.0.1:{PORT}")
        return 0
    if not OLLAMA_EXE.exists():
        print(f"[失败] 找不到 {OLLAMA_EXE}")
        return 1

    env = dict(os.environ)
    env["OLLAMA_MODELS"] = str(PROJECT / "ollama" / "models")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "ab", buffering=0)
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    # 直接起 serve，不启动托盘 app —— 免得它自己又把开机自启加回去
    proc = subprocess.Popen([str(OLLAMA_EXE), "serve"], cwd=str(PROJECT / "ollama" / "app"),
                            stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                            env=env, creationflags=flags, close_fds=True)
    log.close()
    print(f"[启动] Ollama serve PID={proc.pid}，等待就绪…")
    for _ in range(60):
        time.sleep(0.5)
        if healthy():
            print(f"[就绪] http://{HOST}:{PORT}   模型目录 {env['OLLAMA_MODELS']}")
            return 0
    print(f"[警告] 30 秒内没就绪，看日志：{LOG}")
    return 1


def stop() -> int:
    cmd = (
        f"$p = Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue; "
        f"if ($p) {{ $p | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }} }}; "
        "Get-Process 'ollama app' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
    time.sleep(1)
    print("[已停止] Ollama" if not listening() else "[警告] 仍在监听")
    return 0


def status() -> int:
    provider = active_provider()
    print(f"当前启用的档案服务商：{provider or '未配置'}")
    print(f"Ollama 端口 {PORT}：{'监听中' if listening() else '未启动'}"
          f"  接口：{'可用' if healthy() else '不可用'}")
    if healthy():
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/api/tags", timeout=3) as r:
                import json

                models = json.loads(r.read().decode("utf-8")).get("models", [])
                for m in models:
                    print(f"    · {m['name']}  {m['size']/1024/1024/1024:.1f} GB")
        except Exception:
            pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        return status()
    if args.stop:
        return stop()
    return start(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
