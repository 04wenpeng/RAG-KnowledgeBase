# -*- coding: utf-8 -*-
"""命令行问答。

用法：
    python ask.py                          # 进入连续对话
    python ask.py "什么是向量数据库？"      # 单次提问
    python ask.py -k 6 --no-llm "查一下..."  # 调大 Top-K、强制离线模式
"""
from __future__ import annotations

import argparse
import sys

from ragkb.config import TOP_K, embedding_hint, llm_config, setup_stdio
from ragkb.rag import RAGKB


def print_result(result: dict, show_prompt: bool = False) -> None:
    mode = {"llm": "大模型生成", "extractive": "离线抽取式", "no_hit": "未命中"}.get(
        result["mode"], result["mode"]
    )
    print()
    print(f"问 题：{result['question']}")
    print(f"模 式：{mode}")
    if result.get("note"):
        print(f"提 示：{result['note']}")
    print("-" * 68)
    print(result["answer"])
    if result["sources"]:
        print("-" * 68)
        print("参考来源：")
        for s in result["sources"]:
            loc = []
            if s.get("page"):
                loc.append(f"第{s['page']}页")
            if s.get("row") is not None:
                loc.append(f"第{int(s['row']) + 1}行")
            if s.get("sheet"):
                loc.append(str(s["sheet"]))
            where = f"（{'，'.join(loc)}）" if loc else ""
            print(f"  [{s['index']}] {s['source']}{where}  相关度 {s['score']:.3f}")
            print(f"      {s['snippet'][:110]}...")
    if show_prompt:
        print("-" * 68)
        print("【送给大模型的提示词】")
        print(result["prompt"])
    print()


def main() -> int:
    setup_stdio()
    parser = argparse.ArgumentParser(description="RAG 知识库问答")
    parser.add_argument("question", nargs="*", help="问题；留空进入连续对话")
    parser.add_argument("-k", "--top-k", type=int, default=TOP_K)
    parser.add_argument("--no-llm", action="store_true", help="只用离线抽取式回答")
    parser.add_argument("--source", default=None, help="只在某个文件里检索，如 课件.pdf")
    parser.add_argument("--show-prompt", action="store_true", help="打印最终提示词")
    parser.add_argument("--retrieve-only", action="store_true", help="只检索不生成")
    args = parser.parse_args()

    cfg = llm_config()
    print("=" * 68)
    print("  RAG 知识库问答")
    print(f"  嵌入模型 : {embedding_hint()}")
    print(f"  生成模型 : {cfg[2] + ' @ ' + cfg[0] if cfg else '未配置（离线抽取式回答）'}")
    print("=" * 68)

    kb = RAGKB()
    stats = kb.store.stats()
    if not stats["exists"]:
        print("[错误] 索引为空，请先运行： python ingest.py")
        return 1
    print(f"  已加载 {stats['count']} 个块 / {len(stats['files'])} 个文件（{stats['backend']}）\n")

    def handle(q: str) -> None:
        if args.retrieve_only:
            hits = kb.retrieve(q, top_k=args.top_k, source_filter=args.source)
            print(f"\n问题：{q}\n检索到 {len(hits)} 条：")
            for i, h in enumerate(hits, 1):
                print(f"\n[{i}] {h['metadata'].get('source')} "
                      f"第{h['metadata'].get('page', '-')}页  相关度{h['score']}")
                print(h["content"][:300])
            print()
            return
        result = kb.ask(
            q,
            top_k=args.top_k,
            use_llm=not args.no_llm,
            source_filter=args.source,
        )
        print_result(result, args.show_prompt)

    if args.question:
        handle(" ".join(args.question))
        return 0

    print("连续对话模式：直接输入问题，输入 q 退出，输入 stats 看索引信息。\n")
    while True:
        try:
            q = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not q:
            continue
        if q.lower() in ("q", "quit", "exit"):
            print("再见。")
            break
        if q.lower() == "stats":
            for k, v in kb.store.stats().items():
                print(f"  {k}: {v}")
            continue
        handle(q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
