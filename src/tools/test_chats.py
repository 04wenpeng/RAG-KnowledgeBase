# -*- coding: utf-8 -*-
"""对话保存 / 新建 / 恢复 测试。

用法：python tools/test_chats.py 8000
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def call(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


def ok(label, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + label + (f"  {extra}" if extra else ""))
    return bool(cond)


def main() -> int:
    passed = True

    print("1) 新建对话")
    code, res = call("POST", "/api/chats", {})
    cid = (res or {}).get("chat", {}).get("id")
    passed &= ok("POST /api/chats", code == 201 and bool(cid), cid or "")
    passed &= ok("初始标题是「新对话」", res["chat"]["title"] == "新对话")

    print("2) 保存问答往来")
    code, _ = call("POST", f"/api/chats/{cid}/messages",
                   {"role": "me", "content": "什么是向量数据库"})
    passed &= ok("保存用户消息", code == 200)
    code, res = call("POST", f"/api/chats/{cid}/messages",
                     {"role": "ai", "content": "向量数据库是存放向量的数据库。",
                      "mode": "llm", "sources": [
                          {"index": 1, "source": "课件.pdf", "page": 4,
                           "score": 0.91, "snippet": "向量数据库用于存储嵌入向量"}]})
    passed &= ok("保存 AI 回答（含出处）", code == 200, str(res.get("chat", {}).get("count")) + " 条")

    code, res = call("GET", f"/api/chats/{cid}")
    chat = res.get("chat", {})
    passed &= ok("标题自动取首条提问", chat.get("title") == "什么是向量数据库", chat.get("title"))
    passed &= ok("消息按顺序存了两条", len(chat.get("messages", [])) == 2)
    passed &= ok("AI 消息保留了出处", bool(chat["messages"][1].get("sources")))
    passed &= ok("AI 消息保留了模式", chat["messages"][1].get("mode") == "llm")

    print("3) 列表与恢复")
    code, res = call("GET", "/api/chats")
    ids = [c["id"] for c in res.get("chats", [])]
    passed &= ok("会话出现在列表里", cid in ids, f"共 {len(ids)} 个会话")
    passed &= ok("列表带条数与时间",
                 all("count" in c and "updated_at" in c for c in res["chats"]))

    print("4) 重命名 / 删除")
    code, res = call("PUT", f"/api/chats/{cid}", {"title": "向量库笔记"})
    passed &= ok("重命名成功", code == 200 and res["chat"]["title"] == "向量库笔记")
    code, res = call("DELETE", f"/api/chats/{cid}")
    passed &= ok("删除成功", code == 200 and res.get("ok"))
    code, res = call("GET", f"/api/chats/{cid}")
    passed &= ok("删除后取不到", code == 404)

    print("5) 真实问答会自动保存（走 /api/ask + 追加）")
    code, res = call("POST", "/api/chats", {})
    cid2 = res["chat"]["id"]
    code, ans = call("POST", "/api/ask", {"question": "什么是 RAG", "k": 2, "use_llm": False})
    call("POST", f"/api/chats/{cid2}/messages", {"role": "me", "content": "什么是 RAG"})
    call("POST", f"/api/chats/{cid2}/messages",
         {"role": "ai", "content": ans.get("answer", ""), "mode": ans.get("mode"),
          "sources": ans.get("sources", [])})
    code, res = call("GET", f"/api/chats/{cid2}")
    passed &= ok("问答链路能把两条都存下来", len(res["chat"]["messages"]) == 2)
    call("DELETE", f"/api/chats/{cid2}")

    print("\n" + ("对话保存正常 ✅" if passed else "有失败项 ❌"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
