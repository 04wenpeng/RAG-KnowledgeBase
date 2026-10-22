# -*- coding: utf-8 -*-
"""测试"重建索引"与"嵌入模型不一致告警"。用法：python tools/test_web2.py 8000"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def call(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"} if data else {},
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


print("A) 重建索引")
code, res = call("POST", "/api/reindex")
print(f"   HTTP {code} -> {res}")
assert code == 200 and res.get("ok"), "重建失败"

print("B) 重建后 embedder 应与 built_embedder 一致")
code, st = call("GET", "/api/stats")
print(f"   embedder={st['embedder_raw']} built={st['built_embedder']} mismatch={st['embedder_mismatch']}")
assert st["embedder_raw"] == st["built_embedder"], "不一致"
assert st["embedder_mismatch"] is False

print("C) 建一套 dashscope 嵌入配置，应触发不一致告警")
code, created = call("POST", "/api/profiles", {
    "name": "嵌入告警测试", "provider": "dashscope",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus", "api_key": "sk-fakefakefakefakefakefakefake",
    "embedding": "dashscope", "embedding_model": "text-embedding-v1",
})
pid = created["profile"]["id"]
call("POST", f"/api/profiles/{pid}/activate")
code, st = call("GET", "/api/stats")
print(f"   embedder={st['embedder_raw']} built={st['built_embedder']} mismatch={st['embedder_mismatch']}")
assert st["embedder_mismatch"] is True, "没有告警"

print("D) 删掉测试配置，恢复原状")
call("DELETE", f"/api/profiles/{pid}")
code, st = call("GET", "/api/stats")
print(f"   mismatch={st['embedder_mismatch']} llm={st['llm']!r}")
print("\n全部通过 ✅")
