# -*- coding: utf-8 -*-
"""把本地 Ollama 接进知识库：建档案 → 测试 → 启用 → 真问题验证。"""
from __future__ import annotations

import json
import sys
import urllib.request

KB = "http://127.0.0.1:8000"
MODEL = "qwen-local"
BASE_URL = "http://localhost:11434/v1"


def api(method: str, path: str, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(KB + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=300) as r:
        body = r.read().decode("utf-8")
        return json.loads(body) if body else {}


def main() -> int:
    print("1) 查找已有 Ollama 档案")
    profiles = api("GET", "/api/profiles").get("profiles", [])
    target = next((p for p in profiles if p.get("provider") == "ollama"), None)

    payload = {
        "name": "本地模型（Qwen2.5-1.5B）",
        "provider": "ollama",
        "base_url": BASE_URL,
        "model": MODEL,
        "api_key": "",
        "embedding_mode": "offline",
        "embedding_model": "",
        "embedding_key": "",
    }
    if target:
        pid = target["id"]
        api("PUT", f"/api/profiles/{pid}", payload)
        print(f"   已更新档案 {pid}")
    else:
        res = api("POST", "/api/profiles", payload)
        pid = res["profile"]["id"]
        print(f"   已创建档案 {pid}")

    print("2) 测试连通性")
    res = api("POST", f"/api/profiles/{pid}/test")
    print(f"   ok={res.get('ok')}  {res.get('message') or ''}")

    print("3) 启用")
    api("POST", f"/api/profiles/{pid}/activate")
    print("   已启用")

    print("4) 用真问题验证（走本地模型生成）")
    res = api("POST", "/api/ask",
              {"question": "RAG 的优势和挑战是什么", "k": 3, "use_llm": True})
    print(f"   模式: {res.get('mode')}   命中: {len(res.get('sources') or [])} 段")
    print("   回答:", (res.get("answer") or "")[:400])
    if res.get("sources"):
        for s in res["sources"][:3]:
            print(f"     - [{s['index']}] {s['source']} 第{s.get('page')}页  score={s['score']}")
    return 0 if res.get("mode") == "llm" else 1


if __name__ == "__main__":
    sys.exit(main())
