# -*- coding: utf-8 -*-
"""演示"召回数量 K"的影响：同一个问题，取不同 K 时命中哪些块、上下文多大。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.generator import build_context
from ragkb.rag import RAGKB

QUESTION = "课件里讲了哪些文本分割器，它们的参数分别是什么"


def main() -> int:
    kb = RAGKB()
    print("=" * 78)
    print(f"问题：{QUESTION}")
    print("=" * 78)

    for k in (1, 2, 4, 8):
        hits = kb.retrieve(QUESTION, top_k=k)
        ctx = build_context(hits)
        pages = []
        for h in hits:
            m = h["metadata"]
            where = f"第{m['page']}页" if m.get("page") else (m.get("source", "")[:12])
            pages.append(f"{where}({h['score']:.2f})")
        print(f"\nK={k}  返回 {len(hits)} 块 · 上下文 {len(ctx)} 字")
        for i, p in enumerate(pages, 1):
            print(f"    [{i}] {p}")
    print("\n" + "=" * 78)
    print("说明：K 越大 → 上下文越长、覆盖越全，但噪声和 token 成本也越高")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
