# -*- coding: utf-8 -*-
"""本地小模型服务（llama.cpp）：给知识库提供 OpenAI 兼容接口。

不需要 Ollama。模型是魔搭下载的 GGUF 文件，放在 models\\ 里。

用法：
    .venv\\Scripts\\python.exe src\\tools\\local_llm_server.py           启动（后台）
    .venv\\Scripts\\python.exe src\\tools\\local_llm_server.py --foreground
    .venv\\Scripts\\python.exe src\\tools\\local_llm_server.py --stop
    .venv\\Scripts\\python.exe src\\tools\\local_llm_server.py --status
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
MODELS = PROJECT / "models"
PORT = 8080
HOST = "127.0.0.1"
LOG = MODELS / "llm-server.log"


def pick_model(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    if not MODELS.exists():
        return None
    cands = sorted(MODELS.glob("*.gguf"), key=lambda p: p.stat().st_size, reverse=True)
    return cands[0] if cands else None


def listening(port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, port)) == 0


def healthy() -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/v1/models", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def cmd(model: Path, foreground: bool) -> int:
    py = PROJECT / ".venv" / "Scripts" / "python.exe"
    exe = str(py) if py.exists() else sys.executable
    args = [
        exe, "-m", "llama_cpp.server",
        "--model", str(model),
        "--host", HOST, "--port", str(PORT),
        "--n_ctx", "4096",
        "--n_threads", str(max(4, (os.cpu_count() or 8) - 2)),
        "--verbose", "false",
    ]
    print(f"[模型] {model.name}  ({model.stat().st_size/1024/1024:.0f} MB)")
    if foreground:
        print(f"[服务] 前台运行 http://{HOST}:{PORT}/v1  （Ctrl+C 停止）")
        return subprocess.call(args, cwd=str(ROOT))

    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "ab", buffering=0)
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    proc = subprocess.Popen(args, cwd=str(ROOT), stdout=log, stderr=log,
                            stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    log.close()
    print(f"[服务] 后台启动 PID={proc.pid}，加载模型需要几秒到几十秒…")
    for _ in range(120):
        time.sleep(1)
        if healthy():
            print(f"[服务] 就绪：http://{HOST}:{PORT}/v1")
            print(f"       日志：{LOG}")
            return 0
    print(f"[警告] 90 秒内没起来，看日志：{LOG}")
    return 1


def stop() -> int:
    if not listening():
        print("[无需操作] 本地模型服务没在运行")
        return 0
    cmdline = (
        f"$p = Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue; "
        f"if ($p) {{ $p | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}; 'stopped' }}"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", cmdline], capture_output=True)
    print(f"[已停止] 本地模型服务（端口 {PORT}）")
    return 0


def status() -> int:
    ok = healthy()
    print(f"[状态] 端口 {PORT}：{'运行中' if listening() else '未监听'}"
          f"  接口：{'可用' if ok else '不可用'}")
    if ok:
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/v1/models", timeout=3) as r:
                print("       " + r.read().decode("utf-8", "replace")[:300])
        except Exception:
            pass
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--foreground", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        return status()
    if args.stop:
        return stop()
    if listening():
        print(f"[已运行] 端口 {PORT} 已有服务")
        return 0
    model = pick_model(args.model)
    if not model:
        print("❌ models\\ 里没有 .gguf 模型文件，先跑：")
        print("   .venv\\Scripts\\python.exe src\\tools\\fetch_gguf.py")
        return 1
    return cmd(model, args.foreground)


if __name__ == "__main__":
    sys.exit(main())
