# -*- coding: utf-8 -*-
"""真实浏览器交互测试：切换服务商时，名称是否跟着变。

原理：访问 /config?selftest=1 会让页面注入一段自测脚本，模拟真人下拉选择，
再把结果 POST 回 /api/selftest_result，本脚本读回来做断言。

用法：先起服务 python web.py --port 8000
     再运行 .venv\\Scripts\\python.exe tools\\test_ui_flow.py 8000
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str | None:
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def http_json(path: str, method: str = "GET", payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    browser = find_browser()
    if not browser:
        print("跳过：没找到 Edge/Chrome，无法做浏览器交互测试")
        return 0

    # 清空上一次的结果
    http_json("/api/selftest_result", "POST", {"items": []})

    profile_dir = os.path.join(tempfile.gettempdir(), "ragkb-uiflow")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--no-first-run",
        f"--user-data-dir={profile_dir}", "--virtual-time-budget=15000", "--dump-dom",
        f"{BASE}/config?selftest=1",
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)

    result = {}
    for _ in range(20):
        try:
            data = http_json("/api/selftest_result")
            items = data.get("items") or []
            if len(items) >= 5:
                result = dict(i.split("=", 1) for i in items if "=" in i)
                break
        except Exception:
            pass
        time.sleep(0.4)

    if not result:
        print("  ❌ 没拿到浏览器自测结果（页面脚本可能没跑完）")
        return 1

    print("浏览器里实际发生的：")
    for k, v in result.items():
        print(f"    {k:<22} = {v!r}")

    ok = True
    checks = [
        ("打开新增 → 默认服务商是 DeepSeek", result.get("initial_provider") == "deepseek"),
        ("打开新增 → 名称已预填", result.get("initial_name") == "DeepSeek 官方"),
        ("打开新增 → Base URL 已预填", result.get("initial_base_url") == "https://api.deepseek.com/v1"),
        ("打开新增 → 模型名已预填", result.get("initial_model") == "deepseek-chat"),
        ("离线模式下 → 嵌入模型置灰且为空", result.get("initial_embed_disabled") == "true"
                                             and result.get("initial_embed_value") == ""),
        ("离线模式下 → 嵌入专用 Key 置灰", result.get("initial_embed_key_disabled") == "true"),
        ("切到百炼 → 嵌入模型自动填默认值", result.get("dashscope_embed_model") == "text-embedding-v1"),
        ("切到百炼 → 嵌入模型解除置灰", result.get("dashscope_embed_disabled") == "false"),
        ("首次选 DeepSeek → 名称自动填", result.get("deepseek") == "DeepSeek 官方"),
        ("切到百炼 → 名称跟着变", result.get("dashscope") == "阿里云百炼"),
        ("切到 OpenAI → 名称跟着变", result.get("openai") == "OpenAI"),
        ("手改过名称后切服务商 → 不被覆盖", result.get("custom_then_ollama") == "我的自定义名称"),
        ("清空名称后切服务商 → 重新跟随", result.get("cleared_then_deepseek") == "DeepSeek 官方"),
        ("Base URL 跟着服务商切换", result.get("base_url") == "https://api.deepseek.com/v1"),
        ("模型名跟着服务商切换", result.get("model") == "deepseek-chat"),
    ]
    print()
    for label, cond in checks:
        print(("  ✅ " if cond else "  ❌ ") + label)
        ok &= bool(cond)

    print("\n" + ("名称跟随逻辑正确 ✅" if ok else "有失败项 ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
