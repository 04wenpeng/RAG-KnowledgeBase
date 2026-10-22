# -*- coding: utf-8 -*-
"""从魔搭（ModelScope）下载 GGUF 模型，支持断点续传与进度显示。

用法：
    .venv\\Scripts\\python.exe src\\tools\\fetch_gguf.py
    .venv\\Scripts\\python.exe src\\tools\\fetch_gguf.py --file qwen2.5-1.5b-instruct-q4_k_m.gguf
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT / "models"
REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
BASE = "https://modelscope.cn/api/v1/models"
DEFAULT_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"


def url_for(filename: str) -> str:
    return f"{BASE}/{REPO}/repo?Revision=master&FilePath={filename}"


def download(filename: str) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODELS_DIR / filename
    part = dest.with_suffix(dest.suffix + ".part")

    have = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={have}-"} if have else {}
    req = urllib.request.Request(url_for(filename), headers=headers)

    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length") or 0) + have
        mode = "ab" if have else "wb"
        got = have
        t0 = time.time()
        last = 0.0
        with open(part, mode) as fh:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                fh.write(chunk)
                got += len(chunk)
                now = time.time()
                if now - last > 2:
                    last = now
                    speed = (got - have) / max(now - t0, 0.01) / 1024 / 1024
                    pct = (got / total * 100) if total else 0
                    eta = ((total - got) / 1024 / 1024 / speed / 60) if speed > 0.01 else 0
                    print(f"\r  {got/1024/1024:7.1f} / {total/1024/1024:7.1f} MB  "
                          f"{pct:5.1f}%  {speed:5.2f} MB/s  剩余约 {eta:4.1f} 分钟",
                          end="", flush=True)

    part.replace(dest)
    print(f"\n✅ 完成：{dest}  ({dest.stat().st_size/1024/1024:.0f} MB)")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT_FILE)
    args = ap.parse_args()
    try:
        download(args.file)
        return 0
    except KeyboardInterrupt:
        print("\n已中断，下次运行会续传")
        return 1


if __name__ == "__main__":
    sys.exit(main())
