# -*- coding: utf-8 -*-
"""混合检索：向量相似度（课件 P77-P79）+ BM25 关键词重排。

课件 P5 已经点明「检索质量直接决定生成效果」。纯向量检索在中文专有名词、
型号、编号这类查询上经常翻车，所以这里把两路结果融合：

    最终分 = 0.55 * BM25归一化分 + 0.45 * 向量归一化分 + 原串命中加分
    再对链接清单块、代码块做降权，避免它们靠字面重叠「抢答」。
"""
from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

from .config import BM25_B, BM25_K1, SUBSTRING_BONUS, TOP_K, W_BM25, W_VEC
from .embedder import code_ratio, term_counts, terms
from .store import VectorStore

# 仅凭这些词命中不足以证明「库里真的有答案」（问股价匹到「多少」就是这种情况）
_GENERIC_TERMS = {
    "多少", "什么", "怎么", "如何", "为什么", "哪个", "哪些", "是否",
    "可以", "一下", "怎样", "请问", "告诉", "说明",
}


class Retriever:
    def __init__(self, store: VectorStore):
        self.store = store
        self.chunks: list[dict] = store.all_chunks()
        self.index_of: dict[str, int] = {
            str(c.get("id") or i): i for i, c in enumerate(self.chunks)
        }
        self.n = len(self.chunks)

        self.doc_terms: list[Counter] = [Counter(term_counts(c["page_content"])) for c in self.chunks]
        self.doc_len = np.array([sum(t.values()) for t in self.doc_terms], dtype=np.float32)
        self.avgdl = float(self.doc_len.mean()) if self.n else 0.0

        self.df: Counter = Counter()
        self.postings: dict[str, list[tuple[int, int]]] = {}
        for idx, tf in enumerate(self.doc_terms):
            for term, cnt in tf.items():
                self.df[term] += 1
                self.postings.setdefault(term, []).append((idx, cnt))

        # 词权重（IDF）：稀有词命中远比「默认」「什么」这类常用词重要
        self.idf: dict[str, float] = (
            {
                term: math.log(1.0 + (self.n - df + 0.5) / (df + 0.5))
                for term, df in self.df.items()
            }
            if self.n
            else {}
        )

    # ———————————————— BM25 ————————————————
    def _bm25(self, q_terms: list[str]) -> np.ndarray:
        scores = np.zeros(self.n, dtype=np.float32)
        if not self.n or self.avgdl <= 0:
            return scores
        for term in set(q_terms):
            postings = self.postings.get(term)
            if not postings:
                continue
            df = self.df[term]
            idf = math.log(1.0 + (self.n - df + 0.5) / (df + 0.5))
            for idx, tf in postings:
                dl = self.doc_len[idx] or 1.0
                denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / self.avgdl)
                scores[idx] += idf * tf * (BM25_K1 + 1) / denom
        return scores

    # ———————————————— 融合检索 ————————————————
    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        source_filter: str | None = None,
        pool: int | None = None,
    ) -> list[dict]:
        if not query.strip() or not self.n:
            return []

        pool = pool or max(20, top_k * 5)
        vec = np.zeros(self.n, dtype=np.float32)
        for chunk, sim in self.store.query(query, k=pool):
            idx = self.index_of.get(str(chunk.get("id")))
            if idx is not None:
                vec[idx] = max(vec[idx], sim)

        bm25 = self._bm25(terms(query))

        def norm(arr: np.ndarray) -> np.ndarray:
            mx = float(arr.max()) if arr.size else 0.0
            return arr / mx if mx > 0 else arr

        score = W_BM25 * norm(bm25) + W_VEC * norm(vec)

        needle = query.strip().lower()
        if len(needle) >= 3:
            for i, chunk in enumerate(self.chunks):
                text = chunk["page_content"].lower()
                hits = text.count(needle)
                if hits:
                    score[i] += SUBSTRING_BONUS
                # 原句出现太多次 → 多半是示例代码/输出页在复读问题。
                # 但说明文档里「标题 + 常见问法 + 正文」本来就会重复几次，所以门槛放到 4 次。
                if hits >= 4:
                    score[i] *= 0.45 if hits >= 6 else 0.7

        if source_filter:
            for i, chunk in enumerate(self.chunks):
                if source_filter.lower() not in str(chunk["metadata"].get("source", "")).lower():
                    score[i] = 0.0

        # 降权：链接清单（整页都是 URL）与代码块，字面重叠高但往往不是答案。
        # 注意：正常文档里出现 2~3 个链接不该被当成链接清单，否则「怎么给别人用」
        # 这类含链接的说明段落会被打压掉。
        for i, chunk in enumerate(self.chunks):
            text = chunk["page_content"]
            urls = re.findall(r"https?://\S+", text)
            if urls:
                url_chars = sum(len(u) for u in urls)
                ratio = url_chars / max(len(text), 1)
                if len(urls) >= 4 and ratio > 0.35:
                    score[i] *= 0.45          # 真正的链接清单页
                elif len(urls) >= 4:
                    score[i] *= 0.85
            code = code_ratio(text)
            if code > 0.25:
                score[i] *= 0.5
            elif code > 0.1:
                score[i] *= 0.8

        # 只靠「多少 / 什么 / 怎么」这类泛词命中，多半是误召回（例如问股价，
        # 结果匹到课件里「张三和李四分别有多少钱」）。这种情况直接判为没命中。
        # 判定看的是**排名第一的那块**：它必须包含至少一个非泛词，否则不值得送去生成。
        strong_terms = [t for t in set(terms(query)) if t not in _GENERIC_TERMS]
        if strong_terms and np.any(score > 0):
            top_idx = int(np.argmax(score))
            top_text = self.chunks[top_idx]["page_content"]
            if not any(t in top_text for t in strong_terms):
                return []

        picked, seen = [], set()
        for idx in np.argsort(-score)[: pool]:
            s = float(score[int(idx)])
            if s <= 0:
                continue
            chunk = self.chunks[int(idx)]
            meta = chunk.get("metadata", {}) or {}
            # 同一页 / 同一行只保留最相关的一块，让来源更分散
            if meta.get("page"):
                dedup_key = (meta.get("source"), meta.get("page"))
            else:
                dedup_key = chunk["page_content"][:40]
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            picked.append(
                {
                    "id": chunk.get("id"),
                    "content": chunk["page_content"],
                    "metadata": meta,
                    "score": round(s, 4),
                    "bm25": round(float(bm25[int(idx)]), 4),
                    "vector": round(float(vec[int(idx)]), 4),
                }
            )
            if len(picked) >= top_k:
                break
        return picked
