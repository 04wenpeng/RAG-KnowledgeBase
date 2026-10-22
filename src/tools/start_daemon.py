# -*- coding: utf-8 -*-
"""后台启动知识库服务（脱离当前窗口，关掉黑框也不会停）。

用法：8-后台启动.bat   或   .venv\\Scripts\\python.exe tools\\start_daemon.py
日志写到项目根目录的 server.log。
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # src/
PROJECT = ROOT.parent                            # 项目根（.venv、server.log 在这）
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LOG = PROJECT / "server.log"


def port_open(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    if port_open(PORT):
        print(f"[已运行] 端口 {PORT} 上已有服务，直接打开页面。")
        subprocess.Popen(["cmd", "/c", "start", "", f"http://127.0.0.1:{PORT}/"])
        return 0

    exe = PROJECT / ".venv" / "Scripts" / "python.exe"
    if not exe.exists():
        exe = Path(sys.executable)

    flags = 0
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP：与当前控制台完全脱钩
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    log = open(LOG, "ab", buffering=0)
    proc = subprocess.Popen(
        [str(exe), str(ROOT / "web.py"), "--port", str(PORT), "--open", "/"],
        cwd=str(ROOT), stdout=log, stderr=log, stdin=subprocess.DEVNULL,
        creationflags=flags, close_fds=True,
    )
    log.close()

    for _ in range(30):
        time.sleep(0.4)
        if port_open(PORT):
            print(f"[已启动] 后台进程 PID={proc.pid}，端口 {PORT}")
            print(f"         页面：http://127.0.0.1:{PORT}/")
            print(f"         日志：{LOG}")
            print(f"         停止：双击 9-停止服务.bat")
            return 0
    print(f"[警告] 等了 12 秒端口还没起来，看看日志：{LOG}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
