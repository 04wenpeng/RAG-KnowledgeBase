# -*- coding: utf-8 -*-
"""测 ollama 模型仓库的下载速度（不装 Ollama 也能测）。

读 manifest → 取第一层 blob → Range 请求下 8MB → 算速度。
"""
from __future__ import annotations

import json
import time
import urllib.request

REG = "https://registry.ollama.ai/v2/library/qwen3/manifests/4b"


def get(url: str, headers: dict | None = None, limit: int | None = None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        if limit:
            return r.read(limit), r.headers
        return r.read(), r.headers


def main() -> int:
    print("1) 取 manifest")
    raw, _ = get(REG, {"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
    mf = json.loads(raw)
    layers = mf.get("layers", [])
    print(f"   共 {len(layers)} 层")
    for l in layers:
        print(f"   - {l['mediaType'].split('.')[-1]:<12} {l['size']/1024/1024:8.1f} MB  {l['digest'][:20]}")
    model_layer = next((l for l in layers if l["size"] > 50 * 1024 * 1024), layers[-1])
    print(f"\n2) 取最大层测速（{model_layer['size']/1024/1024:.0f} MB）")

    url = f"https://registry.ollama.ai/v2/library/qwen3/blobs/{model_layer['digest']}"
    want = 8 * 1024 * 1024
    start = time.time()
    got, headers = get(url, {"Range": f"bytes=0-{want-1}"}, limit=want)
    cost = time.time() - start
    speed = len(got) / cost / 1024 / 1024 if cost else 0
    print(f"   8MB 用时 {cost:.2f}s  →  {speed:.2f} MB/s")
    if model_layer["size"] / 1024 / 1024 / max(speed, 0.01) < 3600:
        eta = model_layer["size"] / 1024 / 1024 / max(speed, 0.01)
        print(f"   预计完整下载：约 {eta/60:.1f} 分钟")
    else:
        print("   预计完整下载：超过 1 小时，太慢")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
