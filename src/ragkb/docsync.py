# -*- coding: utf-8 -*-
"""把项目自己的说明文档同步进 data/，让知识库能回答"这个库怎么用"。

重建索引时会自动调用（pipeline.build_index），所以改了说明文档之后点一次
「重建索引」就自动进库，不需要额外操作。

单独用也可以：
    .venv\\Scripts\\python.exe src\\tools\\sync_docs_to_data.py           # 同步
    .venv\\Scripts\\python.exe src\\tools\\sync_docs_to_data.py --check   # 只看差异
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
TARGET = DATA / "项目说明"

# (源文件, 目标文件名) —— 只收"这个知识库自己怎么用"的文档。
# README.md 以及 dist/ 下的分发说明故意不收：它们和 FAQ 重叠，
# 实测会把「怎么给别人用」这类问题的答案挤掉。
SOURCES = [
    ("AGENTS.md", "项目说明-给Agent看.md"),
    ("src/README.md", "项目说明-源码索引.md"),
    ("src/agent/README.md", "项目说明-Agent接入.md"),
    ("src/agent/AGENT_INSTRUCTIONS.md", "项目说明-怎么让别的Agent用.md"),
]


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def sync(verbose: bool = False) -> list[str]:
    """同步所有文档，返回被更新的目标文件名列表。"""
    TARGET.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    for rel, name in SOURCES:
        src = ROOT / rel
        if not src.exists():
            if verbose:
                print(f"  [跳过] {rel} 不存在")
            continue
        body = src.read_text(encoding="utf-8")
        text = f"<!-- 由 src/ragkb/docsync.py 从 {rel} 自动同步，请勿手改本文件 -->\n{body}"
        dst = TARGET / name
        old = dst.read_text(encoding="utf-8") if dst.exists() else ""
        if _digest(old) == _digest(text):
            continue
        dst.write_text(text, encoding="utf-8")
        changed.append(name)
        if verbose:
            print(f"  [同步] {rel} -> data/项目说明/{name}")
    return changed


def check() -> list[tuple[str, bool]]:
    """返回 [(目标文件名, 是否有差异)]，不写文件。"""
    out = []
    for rel, name in SOURCES:
        src = ROOT / rel
        if not src.exists():
            continue
        text = f"<!-- 由 src/ragkb/docsync.py 从 {rel} 自动同步，请勿手改本文件 -->\n{src.read_text(encoding='utf-8')}"
        dst = TARGET / name
        old = dst.read_text(encoding="utf-8") if dst.exists() else ""
        out.append((name, _digest(old) != _digest(text)))
    return out
