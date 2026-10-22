# -*- coding: utf-8 -*-
"""网页接口冒烟测试（不需要浏览器）。

用法：先起服务  python web.py --port 8000
     再运行   .venv\\Scripts\\python.exe tools\\test_web.py 8000
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def call(method: str, path: str, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"} if data else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def ok(label, cond, extra=""):
    cond = bool(cond)
    print(("  ✅ " if cond else "  ❌ ") + label + (f"  {extra}" if extra else ""))
    return cond


def main() -> int:
    passed = True

    print("1) 页面")
    code, html = call("GET", "/")
    passed &= ok("GET / 返回问答页", code == 200 and "RAG 知识库" in html)
    code, html2 = call("GET", "/config")
    passed &= ok("GET /config 返回配置页", code == 200 and "API 配置" in html2)

    print("2) 初始状态")
    # 记下当前启用的是哪个档案，测试结束要还原
    snapshot_active = next((x["id"] for x in (call("GET", "/api/profiles")[1].get("profiles") or []) if x.get("active")), None)
    code, prof = call("GET", "/api/profiles")
    passed &= ok("GET /api/profiles", code == 200 and "providers" in prof,
                 f"已有 {len(prof.get('profiles', []))} 套配置")

    print("3) 新增")
    code, created = call("POST", "/api/profiles", {
        "name": "冒烟测试-DeepSeek",
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "sk-0000000000000000000000000000000000000000",
        "embedding": "offline",
    })
    pid = (created.get("profile") or {}).get("id") if isinstance(created, dict) else None
    passed &= ok("POST 新增配置", code == 201 and bool(pid), f"id={pid}")

    print("4) 列表里 Key 必须是掩码")
    code, listing = call("GET", "/api/profiles")
    item = next((p for p in listing.get("profiles", []) if p["id"] == pid), {})
    passed &= ok("Key 不回传明文", item.get("api_key", "") == "" and item.get("api_key_masked", "").count("*") >= 4,
                 item.get("api_key_masked", ""))

    print("5) 启用")
    code, res = call("POST", f"/api/profiles/{pid}/activate")
    passed &= ok("POST 启用", code == 200 and res.get("ok"))

    print("6) 连通性测试（假 Key 应判失败并给出原因）")
    code, res = call("POST", f"/api/profiles/{pid}/test")
    passed &= ok("测试返回结果", code == 200 and "ok" in res,
                 f"ok={res.get('ok')} status={res.get('status')}")
    print("     → " + str(res.get("message", ""))[:110])

    print("7) 修改（模型名 + 留空 Key 表示不改）")
    code, res = call("PUT", f"/api/profiles/{pid}", {"model": "deepseek-reasoner", "api_key": ""})
    updated = (res or {}).get("profile") or {}
    passed &= ok("PUT 修改生效", code == 200 and updated.get("model") == "deepseek-reasoner")

    code, listing = call("GET", "/api/profiles")
    item = next((p for p in listing.get("profiles", []) if p["id"] == pid), {})
    passed &= ok("留空 Key 未清空原 Key", item.get("has_key") is True)

    print("8) 状态接口")
    code, st = call("GET", "/api/stats")
    passed &= ok("GET /api/stats", code == 200 and "count" in st,
                 f"{st.get('count')} 块 / llm={st.get('llm')!r}")

    print("9) 问答接口")
    code, ans = call("POST", "/api/ask", {"question": "什么是向量数据库", "k": 3, "use_llm": False})
    passed &= ok("POST /api/ask", code == 200 and ans.get("sources"),
                 f"mode={ans.get('mode')} sources={len(ans.get('sources') or [])}")

    print("10) 删除")
    code, res = call("DELETE", f"/api/profiles/{pid}")
    if snapshot_active:
        call("POST", f"/api/profiles/{snapshot_active}/activate")   # 还原用户原来的启用项
    passed &= ok("DELETE 删除", code == 200 and res.get("ok"))
    code, listing = call("GET", "/api/profiles")
    passed &= ok("删除后列表里没有它", all(p["id"] != pid for p in listing.get("profiles", [])))

    print("\n" + ("全部通过 ✅" if passed else "有失败项 ❌"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
