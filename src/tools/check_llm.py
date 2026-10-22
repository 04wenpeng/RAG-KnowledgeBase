# -*- coding: utf-8 -*-
"""自检脚本：验证 .env 里的大模型配置是否真的能用。

用法：
    .venv\\Scripts\\python.exe tools\\check_llm.py

它会打印当前选中的服务商 / 地址 / 模型（Key 打码），
然后发一次最小请求，告诉你：通了、还是报什么错。
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.config import embedding_hint, llm_config


def mask(secret: str) -> str:
    if not secret:
        return "<空>"
    if len(secret) <= 10:
        return "****"
    return f"{secret[:5]}****{secret[-4:]}（长度 {len(secret)}）"


def main() -> int:
    cfg = llm_config()
    print("=" * 66)
    print("  大模型配置自检")
    print("=" * 66)
    print(f"  嵌入模型 : {embedding_hint()}")

    if not cfg:
        print("  对话模型 : 未配置")
        print("-" * 66)
        print("  当前是离线抽取式模式（能用，只是回答不润色）。")
        print("  想接大模型：编辑项目根目录 .env，取消注释一种方案并填 Key。")
        return 0

    base_url, api_key, model = cfg
    print(f"  服务地址 : {base_url}")
    print(f"  模型名   : {model}")
    print(f"  API Key  : {mask(api_key)}")
    print("-" * 66)

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "只回复两个字：可用"}],
        "max_tokens": 16,
        "temperature": 0,
        "stream": False,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        answer = body["choices"][0]["message"]["content"].strip()
        print(f"  ✅ 调用成功，耗时 {time.time() - t0:.1f}s")
        print(f"  模型回复 : {answer}")
        print("-" * 66)
        print("  结论：配置可用。现在可以运行  python ask.py \"你的问题\"")
        return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        print(f"  ❌ HTTP {exc.code} {exc.reason}")
        print(f"  返回内容 : {detail}")
        print("-" * 66)
        hints = {
            401: "Key 不对或已失效：去服务商控制台重新复制一次（注意别带空格/换行）。",
            402: "账户余额不足：DeepSeek 需要先充值才能调用。",
            403: "Key 无权访问该模型，或账号未开通。",
            404: "模型名或地址不对：检查 LLM_MODEL / LLM_BASE_URL。",
            429: "触发限流或额度用尽，稍后再试或换方案。",
        }
        print("  可能原因：" + hints.get(exc.code, "看上面返回内容里的 message 字段。"))
        return 1
    except Exception as exc:
        print(f"  ❌ 连接失败：{type(exc).__name__}: {exc}")
        print("-" * 66)
        print("  可能原因：网络不通 / 代理没开 / 地址写错（本地 Ollama 要在运行状态）。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
