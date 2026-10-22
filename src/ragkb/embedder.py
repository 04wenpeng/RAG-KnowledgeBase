# -*- coding: utf-8 -*-
"""向量化模块：离线环境下替代"嵌入模型"（课件 P44 / P77-P78）。

设计说明（重要）：
    课件的嵌入模型是 DashScopeEmbeddings / OllamaEmbeddings，需要联网下载或调 API。
    本机当前无网络，因此这里用「字符 n-gram 哈希向量」做离线替代：
      * 中文按 2gram/3gram 切片，英文/数字按词切片 —— 能抓住字面与近义改写
      * 用 crc32 哈希到固定维度（4096），sublinear TF + L2 归一化
      * 余弦相似度检索，接口与 Chroma 的 embedding_function 一致

    它不是语义向量（不懂"汽车≈轿车"这种），所以在检索层叠加了 BM25 关键词分，
    组成混合检索。配置好 .env 后，可把本模块换成真正的嵌入模型。
"""
from __future__ import annotations

import math
import re
import zlib

import numpy as np

from .config import EMBED_DIM, NGRAM_MAX, NGRAM_MIN

_LATIN_RE = re.compile(r"[a-z0-9_+#.]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")
_PUNCT_RE = re.compile(r"[\s\u3000，。！？；：、“”‘’（）《》【】…—\-·!?,.;:()\[\]{}\"'`~@#$%^&*+=|\\/<>]+")

# 中文停用字：含这些字的 n-gram 信息量极低（"的优""和挑"），会带偏 BM25
_STOP_CHARS = set(
    "的了是在和与及或也就都而其所这那我你他她它们有会能可要对从到为以于之并但很更最等中上下个些么呢吗吧啊么"
    "，。！？；：、（）《》“”‘’ \t\n"
)


def _keep_ngram(gram: str) -> bool:
    hits = sum(1 for ch in gram if ch in _STOP_CHARS)
    if len(gram) == 2:
        return hits == 0
    return hits <= 1


def terms(text: str) -> list[str]:
    """把文本切成检索用的 term 列表（中文 n-gram + 英文单词）。"""
    if not text:
        return []
    low = text.lower()
    out: list[str] = []

    for m in _LATIN_RE.finditer(low):
        tok = m.group(0).strip("._-")
        if len(tok) >= 2:
            out.append(tok)

    for m in _CJK_RE.finditer(low):
        seg = m.group(0)
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            if len(seg) < n:
                continue
            for i in range(len(seg) - n + 1):
                gram = seg[i:i + n]
                if _keep_ngram(gram):
                    out.append(gram)
    return out


def term_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in terms(text):
        counts[t] = counts.get(t, 0) + 1
    return counts


def _hash(term: str) -> int:
    return zlib.crc32(term.encode("utf-8")) % EMBED_DIM


def vectorize_one(text: str) -> np.ndarray:
    vec = np.zeros(EMBED_DIM, dtype=np.float32)
    counts = term_counts(text)
    if not counts:
        return vec
    for term, cnt in counts.items():
        vec[_hash(term)] += 1.0 + math.log(cnt)      # sublinear TF
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec


def vectorize_many(texts, batch_size: int = 256, verbose: bool = False) -> np.ndarray:
    n = len(texts)
    mat = np.zeros((n, EMBED_DIM), dtype=np.float32)
    for i, text in enumerate(texts):
        mat[i] = vectorize_one(text)
        if verbose and (i + 1) % batch_size == 0:
            print(f"    向量化 {i + 1}/{n}")
    return mat


_CODE_CHARS = set("{}[]()=;<>#|$\\/*+")


def code_ratio(text: str) -> float:
    """代码符号占比。用来把"代码块"和"正文"区分开。"""
    if not text:
        return 0.0
    hits = sum(1 for ch in text if ch in _CODE_CHARS)
    return hits / len(text)


class HashingEmbedder:
    """接口对齐 langchain 的 Embeddings（embed_query / embed_documents）。"""

    name = "offline-hashing-ngram"

    def embed_query(self, text: str) -> list[float]:
        return vectorize_one(text).tolist()

    def embed_documents(self, texts) -> list[list[float]]:
        return [vectorize_one(t).tolist() for t in texts]
