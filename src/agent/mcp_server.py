# -*- coding: utf-8 -*-
"""把知识库暴露成 MCP 服务（stdio 传输），任何支持 MCP 的客户端都能用。

支持：Claude Desktop、Cursor、Continue、以及阿里云百炼等支持 MCP 的平台。

配置示例（claude_desktop_config.json / Cursor 的 mcp.json）：

    {
      "mcpServers": {
        "rag-knowledge-base": {
          "command": "E:/RAG-KnowledgeBase/.venv/Scripts/python.exe",
          "args": ["E:/RAG-KnowledgeBase/agent/mcp_server.py"],
          "env": { "RAG_KB_URL": "http://127.0.0.1:8000" }
        }
      }
    }

协议：JSON-RPC 2.0，按行分隔（MCP 的 stdio 传输），实现
      initialize / tools/list / tools/call / ping 四个方法。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag_client import RAGClient  # noqa: E402

SERVER_NAME = "rag-knowledge-base"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"
KB_BASE = os.environ.get("RAG_KB_URL", "http://127.0.0.1:8000")

TOOLS = [
    {
        "name": "ask_knowledge_base",
        "description": (
            "在本地 RAG 知识库里提问，返回带出处的答案。"
            "适合询问公司内部资料、产品文档、课件等知识库中可能存在的内容。"
            "知识库里没有时会明确说无法回答，不会编造。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "用户的完整问题"},
                "top_k": {"type": "integer", "description": "召回片段数，默认 4",
                          "minimum": 1, "maximum": 10},
            },
            "required": ["question"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": (
            "只在知识库里检索原文片段，不做总结。"
            "适合需要阅读原文、核对条款、或自己再推理的场景。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索关键词或短句"},
                "top_k": {"type": "integer", "description": "返回几段，默认 4",
                          "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "knowledge_base_status",
        "description": "查看知识库状态：有多少文件、多少分块、当前用哪个模型。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _client() -> RAGClient:
    return RAGClient(KB_BASE)


# ————————————— 工具实现 —————————————
def tool_ask(args: dict) -> str:
    question = (args.get("question") or "").strip()
    if not question:
        return "缺少 question 参数"
    k = int(args.get("top_k") or 4)
    kb = _client()
    result = kb.ask(question, k=k)
    answer = (result.get("answer") or "").strip()
    srcs = kb.sources_text(result, limit=4)
    return f"{answer}\n\n出处：\n{srcs}" if srcs else answer


def tool_search(args: dict) -> str:
    query = (args.get("query") or "").strip()
    if not query:
        return "缺少 query 参数"
    k = int(args.get("top_k") or 4)
    hits = _client().search(query, k=k)
    if not hits:
        return "知识库里没有检索到相关内容。"
    return "\n\n".join(
        f"[{h['index']}] {h['source']}"
        f"{(' 第' + str(h['page']) + '页') if h.get('page') else ''}"
        f"（相关度 {h['score']}）\n{h['content']}"
        for h in hits
    )


def tool_status(args: dict) -> str:
    stats = _client().health()
    return (f"索引 {stats.get('count')} 块，{len(stats.get('files') or [])} 个文件；"
            f"后端 {stats.get('backend')}；嵌入 {stats.get('embedder')}；"
            f"对话模型 {stats.get('llm') or '未配置'}")


HANDLERS = {
    "ask_knowledge_base": tool_ask,
    "search_knowledge_base": tool_search,
    "knowledge_base_status": tool_status,
}


# ————————————— JSON-RPC —————————————
def _result(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code: int, message: str):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle(req: dict) -> dict | None:
    method = req.get("method")
    msg_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return _result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method in ("notifications/initialized", "initialized"):
        return None                      # 通知不需要回复

    if method == "ping":
        return _result(msg_id, {})

    if method == "tools/list":
        return _result(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            return _error(msg_id, -32602, f"未知工具：{name}")
        try:
            text = handler(args)
        except RuntimeError as exc:
            return _result(msg_id, {
                "content": [{"type": "text", "text": f"知识库不可用：{exc}"}],
                "isError": True,
            })
        return _result(msg_id, {"content": [{"type": "text", "text": text}]})

    if method in ("shutdown", "exit"):
        return _result(msg_id, {}) if msg_id is not None else None

    return _error(msg_id, -32601, f"不支持的方法：{method}")


def main() -> int:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            print(json.dumps(_error(None, -32700, "解析失败"), ensure_ascii=False), flush=True)
            continue

        if isinstance(req, list):        # 批量请求
            replies = [r for r in (handle(m) for m in req) if r is not None]
            if replies:
                print(json.dumps(replies, ensure_ascii=False), flush=True)
            continue

        reply = handle(req)
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
