# -*- coding: utf-8 -*-
"""把知识库包成 LangChain 工具，给 LangChain / LangGraph agent 直接挂上。

用法（在 .venv 里跑）：

    from agent.langchain_tool import TOOLS
    from langgraph.prebuilt import create_react_agent
    from langchain_community.llms.tongyi import Tongyi

    agent = create_react_agent(Tongyi(model="qwen-plus"), TOOLS)
    agent.invoke({"messages": [("user", "公司差旅住宿标准是多少？")]})

两个工具：
    knowledge_base_ask     检索 + 生成，直接给答案（带出处）
    knowledge_base_search  只检索，返回片段原文（适合 agent 自己推理）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from langchain_core.tools import tool  # noqa: E402

from rag_client import RAGClient  # noqa: E402

KB_BASE = os.environ.get("RAG_KB_URL", "http://127.0.0.1:8000")


def _client() -> RAGClient:
    return RAGClient(KB_BASE)


@tool
def knowledge_base_ask(question: str) -> str:
    """在本地知识库里提问，返回带出处的答案。

    当用户问的是公司内部资料、产品文档、课件内容等"知识库里可能有"的问题时用它。
    它只依据知识库内容回答；如果知识库里没有，会明确说无法回答，不会编造。

    Args:
        question: 用户的完整问题，尽量保留原话里的关键名词。
    """
    try:
        result = _client().ask(question)
    except RuntimeError as exc:
        return f"知识库不可用：{exc}"
    answer = result.get("answer", "").strip()
    srcs = _client().sources_text(result, limit=4)
    return f"{answer}\n\n出处：\n{srcs}" if srcs else answer


@tool
def knowledge_base_search(query: str, top_k: int = 4) -> str:
    """在知识库里检索相关片段，不生成总结。

    适合需要自己阅读原文再推理、或需要引用精确条款的场景。

    Args:
        query: 检索关键词或短句。
        top_k: 返回几段，默认 4，最多 10。
    """
    top_k = max(1, min(int(top_k), 10))
    try:
        hits = _client().search(query, k=top_k)
    except RuntimeError as exc:
        return f"知识库不可用：{exc}"
    if not hits:
        return "知识库里没有检索到相关内容。"
    blocks = []
    for h in hits:
        loc = f"第{h['page']}页" if h.get("page") else ""
        blocks.append(f"[{h['index']}] {h['source']} {loc}（相关度 {h['score']}）\n{h['content']}")
    return "\n\n".join(blocks)


TOOLS = [knowledge_base_ask, knowledge_base_search]


if __name__ == "__main__":
    # 自带一个最小验证：python agent/langchain_tool.py "问题"
    q = " ".join(sys.argv[1:]) or "什么是向量数据库？"
    print("== ask ==")
    print(knowledge_base_ask.invoke({"question": q}))
    print("\n== search ==")
    print(knowledge_base_search.invoke({"query": q, "top_k": 2})[:600])
