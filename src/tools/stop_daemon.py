# -*- coding: utf-8 -*-
"""停止知识库后台服务（按端口找进程）。

用法：9-停止服务.bat   或   .venv\\Scripts\\python.exe tools\\stop_daemon.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


def main() -> int:
    if sys.platform != "win32":
        print("这个脚本只处理 Windows")
        return 1
    cmd = (
        f"$p = Get-NetTCPConnection -LocalPort {PORT} -State Listen -ErrorAction SilentlyContinue; "
        f"if ($p) {{ $p | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}; "
        f"'stopped' }} else {{ 'none' }}"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    result = (out.stdout or "").strip()
    if result == "stopped":
        print(f"[已停止] 端口 {PORT} 上的服务已关闭")
    else:
        print(f"[无需操作] 端口 {PORT} 上没有服务在运行")
    stop_ollama()
    return 0


def stop_ollama() -> None:
    """顺手停掉按需启动的本地模型。"""
    script = Path(__file__).resolve().parent / "ensure_ollama.py"
    if script.exists():
        subprocess.run([sys.executable, str(script), "--stop"], capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
