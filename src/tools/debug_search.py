# -*- coding: utf-8 -*-
"""调试脚本：打印检索各分量得分。用法：python tools/debug_search.py "问题" """
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.rag import RAGKB

q = sys.argv[1] if len(sys.argv) > 1 else "RAG 的优势和挑战"
kb = RAGKB()
for h in kb.retriever.search(q, top_k=6):
    m = h["metadata"]
    print(f"p{m.get('page')} score={h['score']} bm25={h['bm25']} vec={h['vector']} len={len(h['content'])}")
    print("    ", h["content"][:80].replace("\n", " "))
