# -*- coding: utf-8 -*-
"""一键打开网页：服务在就直接开浏览器，不在就先启动再开。

用法： python tools/open_page.py [端口] [路径]
      python tools/open_page.py 8000 /config
"""
from __future__ import annotations

import socket
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # src/
PROJECT = ROOT.parent


def listening(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.6)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    path = sys.argv[2] if len(sys.argv) > 2 else "/"
    if not path.startswith("/"):
        path = "/" + path
    url = f"http://127.0.0.1:{port}{path}"

    if listening(port):
        print(f"服务已经在运行，直接打开：{url}")
        webbrowser.open(url)
        return 0

    print(f"服务没在运行，先启动，再自动打开 {url}")
    venv_py = PROJECT / ".venv" / "Scripts" / "python.exe"
    exe = str(venv_py) if venv_py.exists() else sys.executable
    try:
        return subprocess.call(
            [exe, str(ROOT / "web.py"), "--port", str(port), "--open", path],
            cwd=str(ROOT),
        )
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
