# -*- coding: utf-8 -*-
"""文本分割器：对齐课件 P71-P76。

  - RecursiveCharacterTextSplitter：按分隔符优先级递归切分（主力）
  - 中文优化分隔符：。！？；，避免把句子切碎
  - Markdown 标题分割：把 #/## 标题写进 metadata
"""
from __future__ import annotations

import re

from .config import CHUNK_OVERLAP, CHUNK_SIZE, SEPARATORS
from .loaders import clean_text


def _merge(pieces: list[str], sep: str, chunk_size: int) -> list[str]:
    """把碎片贪心合并到不超过 chunk_size。"""
    out, cur = [], []
    for piece in pieces:
        if not piece:
            continue
        candidate = sep.join(cur + [piece]) if cur else piece
        if len(candidate) <= chunk_size or not cur:
            cur.append(piece)
        else:
            out.append(sep.join(cur))
            cur = [piece]
    if cur:
        out.append(sep.join(cur))
    return out


def _split_recursive(text: str, seps: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    if not seps:
        # 没有分隔符可用：硬按字符切
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, rest = seps[0], seps[1:]
    if sep == "":
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    pieces = text.split(sep)
    chunks: list[str] = []
    for merged in _merge(pieces, sep, chunk_size):
        if len(merged) <= chunk_size:
            chunks.append(merged)
        else:
            chunks.extend(_split_recursive(merged, rest, chunk_size))
    return [c for c in chunks if c.strip()]


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for prev, cur in zip(chunks, chunks[1:]):
        tail = prev[-overlap:] if len(prev) > overlap else prev
        out.append(tail + cur)
    return out


def _merge_short(chunks: list[str], min_len: int = 40, max_len: int = 700) -> list[str]:
    """表格/目录页会切出大量只有几个字的碎片，粘进相邻块，避免它们污染检索。"""
    out: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if out and len(chunk) < min_len and len(out[-1]) + len(chunk) <= max_len:
            out[-1] = out[-1] + "\n" + chunk
        else:
            out.append(chunk)
    return out


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: list[str] | None = None,
) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    seps = separators if separators is not None else SEPARATORS
    chunks = _split_recursive(text, seps, chunk_size)
    chunks = _merge_short(chunks, min_len=min(40, chunk_size // 4), max_len=int(chunk_size * 1.4))
    return _add_overlap(chunks, chunk_overlap)


def split_documents(
    docs: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: list[str] | None = None,
) -> list[dict]:
    """Document -> 更小的 Document 块，保留原始 metadata 并补 chunk 序号。

    对 Markdown 走「按标题切」：每个小节单独成块，并把标题写回正文开头。
    短小节如果混在一起会被合并成一个大块，检索时容易把不相干的内容一起送进模型。
    """
    out: list[dict] = []
    for doc in docs:
        base_meta = dict(doc.get("metadata") or {})
        source = str(base_meta.get("source", "unknown"))
        text = doc.get("page_content", "") or ""
        if _is_markdown(source, text):
            for section in split_markdown(text):
                heading = " / ".join(
                    section["metadata"].get(k) for k in ("H1", "H2") if section["metadata"].get(k)
                )
                body = section["page_content"]
                # 标题并入正文，保证块本身自带上下文
                content = f"{heading}\n{body}" if heading else body
                for piece in split_text(content, chunk_size, chunk_overlap, separators):
                    meta = dict(base_meta)
                    meta["source"] = source
                    meta["chunk"] = len(out)
                    if heading:
                        meta["section"] = heading
                    out.append({"page_content": piece, "metadata": meta})
            continue
        for i, piece in enumerate(split_text(text, chunk_size, chunk_overlap, separators)):
            meta = dict(base_meta)
            meta["chunk"] = i
            meta["source"] = source
            out.append({"page_content": piece, "metadata": meta})
    for idx, chunk in enumerate(out):
        chunk["id"] = _make_id(chunk, idx)
    return out


def _is_markdown(source: str, text: str) -> bool:
    """只按扩展名判断。

    早期版本还会看正文里有没有 `# 标题`，结果把 PDF 里的 Python 注释
    （`# 定义一个模板`）误判成 Markdown 标题，整个课件被切碎、页码错乱。
    """
    return source.lower().endswith((".md", ".markdown"))


def _make_id(chunk: dict, idx: int) -> str:
    meta = chunk["metadata"]
    locate = meta.get("page") or meta.get("row") or meta.get("sheet") or 1
    return f"{meta.get('source', 'doc')}#{locate}#{meta.get('chunk', 0)}#{idx}"


# —————————— Markdown 标题分割（课件 P75-P76）——————————
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)


def split_markdown(text: str, headers_to_split_on=None) -> list[dict]:
    """按 #/## 标题切分，标题路径写入 metadata；strip_headers=False 时标题留在正文里。"""
    headers_to_split_on = headers_to_split_on or [("#", "H1"), ("##", "H2")]
    level_map = {h[0]: h[1] for h in headers_to_split_on}
    max_level = max(len(h[0]) for h in headers_to_split_on)

    docs: list[dict] = []
    stack: dict[int, str] = {}
    buf: list[str] = []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            meta = {name: stack[lvl] for lvl, name in level_map.items() if lvl in stack}
            docs.append({"page_content": body, "metadata": meta})
        buf.clear()

    for line in text.splitlines():
        m = _HEADER_RE.match(line)
        if m and len(m.group(1)) <= max_level:
            flush()
            level = len(m.group(1))
            stack = {k: v for k, v in stack.items() if k < level}
            if level in level_map:
                stack[level] = m.group(2).strip()
            buf.append(line)
        else:
            buf.append(line)
    flush()
    return docs
