# -*- coding: utf-8 -*-
"""向量存储：优先用 Chroma（课件 P78-P79），无依赖时退化为 numpy 索引。

  store/chroma/         Chroma 持久化目录（chroma 可用时）
  store/meta.json       numpy 后端的分块正文
  store/vectors.npy     numpy 后端的向量矩阵

两个后端对外接口一致：add / query / all_chunks / count / clear / stats，
所以上层 rag.py、retriever.py 不需要关心用的是哪个。
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION,
    EMBED_DIM,
    STORE_DIR,
    embeddings_backend,
)

VERSION = 1


def clear_store(store_dir: Path | None = None) -> None:
    """在建 VectorStore 之前调用：彻底删掉索引目录（Chroma 有文件句柄，必须先关）。"""
    d = Path(store_dir or STORE_DIR)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


class VectorStore:
    def __init__(self, store_dir: Path | None = None, embeddings=None):
        self.dir = Path(store_dir or STORE_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir = self.dir / "chroma"
        self.meta_path = self.dir / "meta.json"
        self.vec_path = self.dir / "vectors.npy"
        self.embeddings = embeddings or embeddings_backend()
        self.embedder_name = getattr(self.embeddings, "name", type(self.embeddings).__name__)
        self.embedder_file = self.dir / "embedder.json"

        self._chroma = None
        try:
            from langchain_chroma import Chroma

            self._chroma = Chroma(
                collection_name=COLLECTION,
                embedding_function=self.embeddings,
                persist_directory=str(self.chroma_dir),
            )
            self.backend = "chroma"
        except Exception:
            self.backend = "numpy"

    # ————————————————— 写入 —————————————————
    def add(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        n = self._add_inner(chunks)
        # 记下建索引用的嵌入模型，换模型时网页能提醒"必须重建"
        try:
            self.embedder_file.write_text(
                json.dumps(
                    {"embedder": self.embedder_name,
                     "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass
        return n

    def _add_inner(self, chunks: list[dict]) -> int:
        if self.backend == "chroma":
            from langchain_core.documents import Document

            ids = [c.get("id") for c in chunks]
            # 已存在的 id 先删再写：重复建库不会产生重复条目，文档改动也能覆盖
            try:
                self._chroma.delete(ids=ids)
            except Exception:
                pass
            docs = [
                Document(
                    page_content=c["page_content"],
                    metadata={**(c.get("metadata") or {}), "chunk_id": c.get("id")},
                    id=c.get("id"),
                )
                for c in chunks
            ]
            self._chroma.add_documents(documents=docs, ids=ids)
            return len(docs)

        from .embedder import vectorize_many

        vectors = vectorize_many([c["page_content"] for c in chunks], verbose=True)
        meta = {
            "version": VERSION,
            "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "embedder": self.embedder_name,
            "embed_dim": int(vectors.shape[1]),
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "count": len(chunks),
            "files": sorted({c["metadata"].get("source", "?") for c in chunks}),
            "chunks": [
                {"id": c.get("id"), "page_content": c["page_content"], "metadata": c.get("metadata", {})}
                for c in chunks
            ],
        }
        tmp = self.meta_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.meta_path)
        tmpv = self.vec_path.with_suffix(".npy.tmp")
        with open(tmpv, "wb") as fh:      # 用文件对象，避免 numpy 自动补 .npy
            np.save(fh, vectors.astype(np.float32))
        tmpv.replace(self.vec_path)
        return len(chunks)

    # ————————————————— 检索 —————————————————
    def query(self, text: str, k: int = 20) -> list[tuple[dict, float]]:
        """返回 [(chunk, 相似度)]，相似度越大越像（0~1 区间左右）。"""
        if self.backend == "chroma":
            try:
                pairs = self._chroma.similarity_search_with_score(text, k=k)
            except Exception:
                return []
            out = []
            for doc, distance in pairs:
                sim = 1.0 / (1.0 + float(distance))
                out.append(
                    (
                        {
                            "id": (doc.metadata or {}).get("chunk_id"),
                            "page_content": doc.page_content,
                            "metadata": doc.metadata or {},
                        },
                        sim,
                    )
                )
            return out

        chunks = self.all_chunks()
        if not chunks or not self.vec_path.exists():
            return []
        from .embedder import vectorize_one

        vectors = np.load(self.vec_path)
        q = vectorize_one(text)
        sims = vectors @ q
        order = np.argsort(-sims)[:k]
        return [(chunks[int(i)], float(sims[int(i)])) for i in order]

    def all_chunks(self) -> list[dict]:
        if self.backend == "chroma":
            try:
                data = self._chroma.get(include=["documents", "metadatas"])
            except Exception:
                return []
            ids = data.get("ids") or []
            docs = data.get("documents") or []
            metas = data.get("metadatas") or []
            out = []
            for i, cid in enumerate(ids):
                out.append(
                    {
                        "id": cid,
                        "page_content": docs[i] if i < len(docs) else "",
                        "metadata": metas[i] if i < len(metas) and metas[i] else {},
                    }
                )
            return out

        if not self.meta_path.exists():
            return []
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return meta.get("chunks", [])

    # ————————————————— 统计 / 清理 —————————————————
    def count(self) -> int:
        if self.backend == "chroma":
            try:
                return int(self._chroma._collection.count())
            except Exception:
                try:
                    return len(self.all_chunks())
                except Exception:
                    return 0
        return len(self.all_chunks())

    def clear(self) -> None:
        if self.chroma_dir.exists():
            shutil.rmtree(self.chroma_dir, ignore_errors=True)
        for p in (self.meta_path, self.vec_path, self.embedder_file):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
        if self.backend == "chroma":
            self.__init__(self.dir, self.embeddings)

    def reset_contents(self) -> None:
        """清空索引内容但保留已打开的连接（网页里正在跑时用这个）。

        Windows 上目录还开着就删不掉，所以不能靠删目录：
        Chroma 走 reset_collection()，numpy 后端删掉向量和元数据文件。
        """
        if self.backend == "chroma":
            try:
                self._chroma.reset_collection()
                return
            except Exception:
                try:
                    from langchain_chroma import Chroma

                    self._chroma.delete_collection()
                    self._chroma = Chroma(
                        collection_name=COLLECTION,
                        embedding_function=self.embeddings,
                        persist_directory=str(self.chroma_dir),
                    )
                    return
                except Exception:
                    pass
        for p in (self.meta_path, self.vec_path, self.embedder_file):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

    def built_embedder(self) -> str:
        """建索引时用的嵌入模型名（读不到就空）。"""
        try:
            if self.embedder_file.exists():
                return json.loads(self.embedder_file.read_text(encoding="utf-8")).get("embedder", "")
        except Exception:
            pass
        return ""

    def stats(self) -> dict:
        chunks = self.all_chunks()
        total_chars = sum(len(c.get("page_content", "")) for c in chunks)
        built_at, chunk_size, overlap = "", CHUNK_SIZE, CHUNK_OVERLAP
        if self.backend == "numpy" and self.meta_path.exists():
            m = json.loads(self.meta_path.read_text(encoding="utf-8"))
            built_at = m.get("built_at", "")
            chunk_size = m.get("chunk_size", chunk_size)
            overlap = m.get("chunk_overlap", overlap)
        return {
            "exists": bool(chunks),
            "backend": self.backend,
            "embedder": self.embedder_name,
            "built_embedder": self.built_embedder(),
            "count": len(chunks),
            "files": sorted({c["metadata"].get("source", "?") for c in chunks}),
            "total_chars": total_chars,
            "chunk_size": chunk_size,
            "chunk_overlap": overlap,
            "built_at": built_at,
        }
