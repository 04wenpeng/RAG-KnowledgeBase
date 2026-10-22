# -*- coding: utf-8 -*-
"""答案质量回归：12 个典型问题，覆盖课件类 / 操作类 / 库外拒答。

用法：python src/tools/test_quality.py 8000
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"

REFUSE = ("无法回答", "无法直接回答", "没有检索到", "没有找到", "无法从", "没有直接提供")

# (类型, 问题, 期望关键词[任一出现即算对])
CASES = [
    ("课件", "chunk_size 默认值多少", ["4000"]),
    ("课件", "召回数量怎么调", ["4", "6", "8"]),
    ("课件", "RAG 的优势和挑战", ["幻觉", "更新", "可解释"]),
    ("课件", "什么是向量数据库", ["向量"]),
    ("操作", "怎么给别人用", ["链接"]),
    ("操作", "怎么备份", ["backup", "备份"]),
    ("操作", "重启后会自动起来吗", ["不会", "手动"]),
    ("操作", "支持哪些文件格式", ["pdf", "docx"]),
    ("操作", "怎么换模型", ["config", "启用"]),
    ("库外", "今天股价多少", None),
    ("库外", "帮我写一首诗", None),
    ("库外", "公司年假几天", None),
]


def ask(question: str, k: int = 4) -> dict:
    body = json.dumps({"question": question, "k": k}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/api/ask", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"answer": f"HTTP {e.code}", "mode": "error", "sources": []}


def main() -> int:
    passed = 0
    for kind, question, expect in CASES:
        d = ask(question)
        ans = (d.get("answer") or "").strip()
        head = ans[:30]
        refused = any(k in head for k in REFUSE)

        if expect is None:
            ok = refused
            extra = "（应拒答）"
        else:
            ok = (not refused) and any(k.lower() in ans.lower() for k in expect)
            extra = "（应给出 " + "/".join(expect) + "）"

        passed += ok
        print(f"  {'✅' if ok else '❌'} [{kind}] {question}{extra}")
        print(f"       {ans.replace(chr(10), ' ')[:90]}")

    total = len(CASES)
    print(f"\n质量回归：{passed}/{total} 通过" + (" ✅" if passed == total else " ❌"))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
