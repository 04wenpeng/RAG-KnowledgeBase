# -*- coding: utf-8 -*-
"""建库流水线：加载 → 分割 → 向量化 → 入库。

ingest.py、网页"重建索引"和网页上传共用。
支持只处理指定文件（上传单个文件时不必全量重算，省时间也省嵌入 API 费用）。
"""
from __future__ import annotations

from pathlib import Path

from .config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR, SEPARATORS
from .loaders import load_all, load_file
from .sources import external_files
from .splitters import split_documents
from .store import VectorStore


def build_index(
    data_dir: str | Path | None = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    reset: bool = False,
    verbose: bool = False,
    files: list[str | Path] | None = None,
) -> dict:
    """建索引。

    files 传了就只处理这几个文件（增量上传场景），否则处理整个 data 目录。
    reset=True 先清空索引；增量场景不要用它。
    """
    data_dir = Path(data_dir or DATA_DIR)

    if files:
        docs = []
        for item in files:
            # 支持 (路径, 来源标签) 形式：导入整个文件夹时，来源里带上相对路径
            if isinstance(item, (tuple, list)):
                path, label = Path(item[0]), item[1]
            else:
                path, label = Path(item), None
            try:
                got = load_file(path)
            except Exception as exc:
                return {"ok": False, "error": f"{path.name} 解析失败：{exc}",
                        "documents": 0, "chunks": 0, "files": 0}
            if verbose:
                print(f"  {str(label or path.name):<40} -> {len(got):>4} 个 Document")
            if label:
                for d in got or []:
                    d.setdefault("metadata", {})["source"] = label
            docs.extend(got or [])
        if not docs:
            return {"ok": False, "error": "这些文件里没有解析出文本内容",
                    "documents": 0, "chunks": 0, "files": 0}
    else:
        # 全量重建前，先把项目说明文档同步进 data/：
        # 这样改了 README/AGENTS/FAQ 之类的说明后，点一次「重建索引」就自动进库。
        try:
            from .docsync import sync as sync_docs

            synced = sync_docs(verbose=verbose)
            if synced and verbose:
                print(f"  [文档同步] {len(synced)} 个说明文档已更新到 data/项目说明/")
        except Exception as exc:
            if verbose:
                print(f"  [文档同步] 跳过（{exc}）")

        docs = load_all(data_dir, verbose=verbose)
        # 把"存在但被过滤掉"的文件记下来，网页上能看到原因
        try:
            from .loaders import skipped_files
            from .skips import record

            for p, reason in skipped_files(data_dir):
                record(p.name, reason)
                if verbose:
                    print(f"  [跳过] {p.name}：{reason}")
        except Exception:
            pass
        # 外部登记过的文件夹也要一起读，否则重建索引会把它们丢掉
        ext = external_files()
        for path, label in ext:
            try:
                got = load_file(path)
            except Exception:
                continue
            for d in got or []:
                d.setdefault("metadata", {})["source"] = label
            if verbose:
                print(f"  {label:<40} -> {len(got):>4} 个 Document (外部)")
            docs.extend(got or [])
        if not docs:
            return {
                "ok": False,
                "error": f"{data_dir} 里没有可解析的文档（支持 pdf/docx/txt/md/csv/xlsx/json）",
                "documents": 0,
                "chunks": 0,
                "files": 0,
            }

    chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                             separators=SEPARATORS)

    store = VectorStore()
    if reset:
        # 用"清空集合内容"而不是删目录：网页服务可能正开着同一个 Chroma，
        # Windows 上目录删不掉，删目录会静默失败并留下旧数据。
        try:
            store.reset_contents()
        except Exception:
            pass

    written = store.add(chunks)
    stats = store.stats()

    return {
        "ok": True,
        "documents": len(docs),
        "chunks": written,
        "files": len(stats.get("files", [])),
        "backend": stats.get("backend"),
        "embedder": stats.get("embedder"),
        "built_embedder": stats.get("built_embedder"),
        "total_chars": stats.get("total_chars", 0),
        "stats": stats,
    }
