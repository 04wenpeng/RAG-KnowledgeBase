# -*- coding: utf-8 -*-
"""演示"嵌入模型"到底在干什么：把文本变成向量，看相似度。

用法： .venv\\Scripts\\python.exe tools\\demo_embedding.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.config import embedding_hint
from ragkb.embedder import HashingEmbedder, vectorize_one


def cos(a, b) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return float(va @ vb / (na * nb)) if na and nb else 0.0


def main() -> int:
    print("=" * 66)
    print("  当前生效的嵌入方案：", embedding_hint())
    print("=" * 66)

    emb = HashingEmbedder()
    v = vectorize_one("什么是向量数据库")
    print(f"\n一句话被变成了 {len(v)} 个数字的向量（前 8 个）：")
    print("  ", np.round(v[:8], 4).tolist())
    print(f"  非零位 {int((v != 0).sum())} 个，其余都是 0（稀疏）")

    pairs = [
        ("完全同义，但一个字都不重合", "电脑坏了怎么办", "计算机故障如何处理"),
        ("同义但不同词", "汽车", "轿车"),
        ("字面高度重合", "什么是向量数据库", "向量数据库是做什么的"),
        ("部分重合（都有“轮胎”）", "汽车轮胎怎么换", "轿车轮胎的更换方法"),
        ("同词不同事", "汽车轮胎怎么换", "汽车发动机异响"),
        ("毫无关系", "什么是向量数据库", "今天天气不错"),
        ("缩写 vs 全称", "RAG 是什么", "检索增强生成是什么"),
        ("术语 vs 大白话", "chunk_size 默认值", "分块大小默认多少"),
    ]
    print("\n两条文本的向量相似度（越接近 1 越像）：")
    for label, a, b in pairs:
        print(f"  {cos(emb.embed_query(a), emb.embed_query(b)):>6.3f}  {label}")
        print(f"          {a}  ↔  {b}")

    print("""
看出来的规律：离线哈希向量算的是"字面重合度"，不是"意思"。
  · 电脑 / 计算机、汽车 / 轿车、RAG / 检索增强生成 —— 一个字都不重合，相似度 0，
    它会认为这些说的是两件不相干的事（真实嵌入模型会给很高的分数）。
  · 只要共享一些字（轮胎、向量数据库），分数就上来了，哪怕换了个说法。

所以：不配嵌入模型也能用（靠字面 + BM25 关键词兜底），但要问得"口语化"、
术语和文档不一致时，就容易召不回东西。升级到真嵌入模型，就是为了让
"意思相近"能被认出来。
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
