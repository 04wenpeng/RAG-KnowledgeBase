# -*- coding: utf-8 -*-
"""RAG 知识库（离线可用版）。

模块对应关系（对照课件）：
    loaders.py    P60-P70   文档加载器 -> Document
    splitters.py  P71-P76   文本分割器
    embedder.py   P44       嵌入模型（离线替代实现）
    store.py      P77-P79   向量存储（Chroma 优先）
    retriever.py  P77-P79   相似度检索（叠 BM25 混合检索）
    generator.py  P80-P83   增强 + 生成
    rag.py        P80-P83   RAG 主流程（RetrievalQA 等价）
"""
from .config import setup_stdio
from .rag import RAGKB
from .store import VectorStore

__all__ = ["RAGKB", "VectorStore", "setup_stdio"]
__version__ = "1.0.0"
