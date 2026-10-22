# -*- coding: utf-8 -*-
"""验证 Agent 接入层：HTTP 客户端、LangChain 工具、MCP 服务。

用法：python tools/test_agent_api.py 8000
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # src/
sys.path.insert(0, str(ROOT / "agent"))

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def ok(label, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + label + (f"  {extra}" if extra else ""))
    return bool(cond)


def main() -> int:
    from rag_client import RAGClient

    passed = True
    kb = RAGClient(BASE)

    print("1) Python 客户端")
    stats = kb.health()
    passed &= ok("health 能拿到索引状态", "count" in stats,
                 f"{stats.get('count')} 块")
    hits = kb.search("什么是向量数据库", k=2)
    passed &= ok("search 返回片段", len(hits) == 2, f"{len(hits)} 条")
    passed &= ok("片段带正文和出处", all(h.get("content") and h.get("source") for h in hits))
    res = kb.ask("什么是向量数据库", k=2, use_llm=False)
    passed &= ok("ask 返回答案", bool(res.get("answer")),
                 f"mode={res.get('mode')}")
    passed &= ok("ask 带出处文本", "课件" in kb.sources_text(res) or bool(res.get("sources")))

    print("2) 命令行客户端")
    out = subprocess.run(
        [sys.executable, str(ROOT / "agent" / "rag_client.py"), "--health"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    passed &= ok("rag_client.py --health 可执行", out.returncode == 0 and "count" in out.stdout)

    print("3) LangChain 工具")
    try:
        os.environ["RAG_KB_URL"] = BASE
        from langchain_tool import TOOLS  # noqa: E402

        names = [t.name for t in TOOLS]
        passed &= ok("工具已注册", names == ["knowledge_base_ask", "knowledge_base_search"],
                     "、".join(names))
        text = TOOLS[1].invoke({"query": "向量数据库", "top_k": 2})
        passed &= ok("search 工具能返回片段", "相关度" in text)
        text2 = TOOLS[0].invoke({"question": "什么是向量数据库"})
        passed &= ok("ask 工具能返回答案", len(text2) > 20)
    except Exception as exc:
        passed &= ok("LangChain 工具可用", False, f"{type(exc).__name__}: {exc}")

    print("4) MCP 服务（stdio JSON-RPC）")
    mcp = [sys.executable, str(ROOT / "agent" / "mcp_server.py")]
    env = dict(os.environ, RAG_KB_URL=BASE)

    def rpc(messages: list[dict]) -> list[dict]:
        payload = "\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n"
        p = subprocess.run(mcp, input=payload, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120, env=env)
        return [json.loads(line) for line in p.stdout.splitlines() if line.strip()]

    replies = rpc([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}])
    passed &= ok("initialize 握手", bool(replies) and replies[0]["result"]["serverInfo"]["name"],
                 replies[0]["result"]["serverInfo"]["name"] if replies else "")

    replies = rpc([{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
    tools = replies[0]["result"]["tools"] if replies else []
    passed &= ok("tools/list 返回 3 个工具", len(tools) == 3,
                 "、".join(t["name"] for t in tools))
    passed &= ok("工具带 inputSchema", all("inputSchema" in t for t in tools))

    replies = rpc([{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "search_knowledge_base",
                               "arguments": {"query": "向量数据库", "top_k": 2}}}])
    content = replies[0]["result"]["content"][0]["text"] if replies else ""
    passed &= ok("tools/call 真能查到内容", "相关度" in content, content[:60].replace("\n", " "))

    replies = rpc([{"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                    "params": {"name": "knowledge_base_status", "arguments": {}}}])
    text = replies[0]["result"]["content"][0]["text"] if replies else ""
    passed &= ok("status 工具返回索引信息", "索引" in text, text[:50])

    replies = rpc([{"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                    "params": {"name": "不存在的工具", "arguments": {}}}])
    passed &= ok("未知工具返回错误", bool(replies) and "error" in replies[0])

    print("\n" + ("Agent 接入层正常 ✅" if passed else "有失败项 ❌"))
    print("\n接入方式：HTTP /api/ask|/api/search · agent/rag_client.py · "
          "agent/langchain_tool.py · agent/mcp_server.py")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
