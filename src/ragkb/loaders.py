# -*- coding: utf-8 -*-
"""文档加载器：把各种文件统一成 LangChain 风格的 Document。

对应课件 P60-P70：
  Document = { page_content: 正文, metadata: {source, page/row/sheet} }
支持格式：pdf / docx / txt / md / csv / xlsx / json
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .config import DATA_DIR
from .pdf_reader import extract_pdf

SUPPORTED = {".pdf", ".docx", ".txt", ".md", ".markdown", ".csv", ".xlsx", ".json"}
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# —— 加入知识库前的过滤：日志、临时文件、校验清单这类东西只会污染检索 ——
SKIP_SUFFIXES = {".log", ".tmp", ".bak", ".lock", ".pyc", ".min", ".map", ".cache", ".swp"}
SKIP_NAME_HINTS = ("md5", "checksum", "crc32")
MAX_FILE_MB = 50            # 单文件上限
MAX_TEXT_MB = 0.5           # 纯文本超过这个大小基本是日志/导出物
LOG_MIN_SIZE_KB = 100       # 小于这个体积不做"内容像日志"判定，避免误伤带日期的记录

# 形如 "T3024 000:004.495"、"2026-10-20 21:12:34"、"[2026-10-20 ...]"、
# "12:03:45" 的行首，出现在大多数行里就认定是日志
_LOG_LINE_RE = re.compile(
    r"^\s*(\[?\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}:\d{2}:\d{2}|[A-Za-z]?\d+\s+\d{3}:\d{3}[.:]\d{3})"
)


def _looks_like_log(path: Path, sample_kb: int = 64) -> bool:
    """抽前 64KB 看行首：大量时间戳行 = 日志。

    只对 ≥100KB 的文件做这个判断——小文件里"每行以日期开头"更可能是
    值班记录、变更日志这种正常资料，不值得为几百行去误伤它。
    """
    try:
        size_kb = path.stat().st_size / 1024
    except OSError:
        return False
    if size_kb < LOG_MIN_SIZE_KB:
        return False
    try:
        with open(path, "rb") as fh:
            raw = fh.read(sample_kb * 1024)
    except OSError:
        return False
    text = raw.decode("utf-8", "replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 200:
        return False
    stamped = sum(1 for ln in lines if _LOG_LINE_RE.match(ln))
    return stamped / len(lines) >= 0.6


def is_ingestible(path: Path) -> tuple[bool, str]:
    """判断一个文件该不该进知识库，返回 (是否可以, 原因)。"""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return False, f"{suffix} 是日志/临时文件"
    if suffix not in SUPPORTED:
        return False, "不支持的格式"
    low = p.name.lower()
    if any(h in low for h in SKIP_NAME_HINTS):
        return False, "疑似校验清单"
    if p.stem.lower().endswith("log"):
        return False, "文件名像日志"
    try:
        size_mb = p.stat().st_size / 1024 / 1024
    except OSError:
        return False, "读不到文件"
    if size_mb > MAX_FILE_MB:
        return False, f"文件 {size_mb:.0f}MB 超过 {MAX_FILE_MB}MB 上限"
    if suffix in (".txt", ".md", ".markdown", ".csv"):
        if size_mb > MAX_TEXT_MB:
            return False, f"纯文本 {size_mb:.1f}MB，超过上限 {MAX_TEXT_MB}MB"
        if _looks_like_log(p):
            return False, "内容像日志（多数行带时间戳）"
    return True, ""


def make_doc(content: str, **metadata) -> dict:
    content = (content or "").strip()
    return {"page_content": content, "metadata": metadata}


# ————————————————— PDF —————————————————
def load_pdf(path: Path) -> list[dict]:
    pages = extract_pdf(path)
    if not pages:
        raise RuntimeError(
            f"无法解析 PDF（可能加密或使用了对象流压缩）：{path.name}\n"
            f"  联网后可执行 pip install pypdf，改用 PyPDFLoader。"
        )
    return [
        make_doc(text, source=path.name, page=no, doc_type="pdf")
        for no, text in pages
    ]


# ————————————————— DOCX —————————————————
def load_docx(path: Path) -> list[dict]:
    parts = []
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    for para in root.iter(f"{_W}p"):
        text = "".join(node.text or "" for node in para.iter(f"{_W}t"))
        if text.strip():
            parts.append(text.strip())
    content = "\n".join(parts)
    return [make_doc(content, source=path.name, doc_type="docx")] if content else []


# ————————————————— 纯文本 / Markdown —————————————————
def load_text(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8", errors="replace")
    doc_type = "markdown" if path.suffix.lower() in (".md", ".markdown") else "text"
    return [make_doc(content, source=path.name, doc_type=doc_type)] if content.strip() else []


# ————————————————— CSV：一行一个 Document（课件 P62）—————————————————
def load_csv(path: Path) -> list[dict]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", "replace")

    docs = []
    reader = csv.DictReader(io.StringIO(text))
    for row_no, row in enumerate(reader):
        pairs = [f"{k}: {v}" for k, v in row.items() if k and str(v or "").strip()]
        if not pairs:
            continue
        docs.append(
            make_doc("；".join(pairs), source=path.name, row=row_no, doc_type="csv")
        )
    return docs


# ————————————————— Excel：一个工作表一个 Document —————————————————
def load_xlsx(path: Path) -> list[dict]:
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise RuntimeError("解析 xlsx 需要 openpyxl（本项目内置 Python 已自带）")

    wb = load_workbook(path, read_only=True, data_only=True)
    docs = []
    for ws in wb.worksheets:
        lines = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if cells:
                lines.append(" | ".join(cells))
        if lines:
            docs.append(
                make_doc("\n".join(lines), source=path.name, sheet=ws.title, doc_type="xlsx")
            )
    wb.close()
    return docs


# ————————————————— JSON —————————————————
def load_json(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return load_text(path)

    items = data if isinstance(data, list) else [data]
    docs = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            text = "；".join(f"{k}: {v}" for k, v in item.items() if str(v).strip())
        else:
            text = str(item)
        if text.strip():
            docs.append(make_doc(text, source=path.name, row=i, doc_type="json"))
    return docs


_LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_text,
    ".md": load_text,
    ".markdown": load_text,
    ".csv": load_csv,
    ".xlsx": load_xlsx,
    ".json": load_json,
}


def load_file(path: Path) -> list[dict]:
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        return []
    return loader(path)


def iter_data_files(data_dir: Path | None = None) -> Iterable[Path]:
    data_dir = Path(data_dir or DATA_DIR)
    for p in sorted(data_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name.startswith(("~$", ".")):
            continue
        ok, _reason = is_ingestible(p)
        if ok:
            yield p


def skipped_files(data_dir: Path | None = None) -> list[tuple[Path, str]]:
    """data 目录里存在、但判定为不该入库的文件及原因。"""
    data_dir = Path(data_dir or DATA_DIR)
    out: list[tuple[Path, str]] = []
    if not data_dir.exists():
        return out
    for p in sorted(data_dir.rglob("*")):
        if not p.is_file() or p.name.startswith(("~$", ".")):
            continue
        if p.suffix.lower() not in SUPPORTED and p.suffix.lower() not in SKIP_SUFFIXES:
            continue
        ok, reason = is_ingestible(p)
        if not ok:
            out.append((p, reason))
    return out


def load_all(data_dir: Path | None = None, verbose: bool = True) -> list[dict]:
    docs: list[dict] = []
    skipped: list[tuple[str, str]] = []
    root = Path(data_dir or DATA_DIR)
    for path in iter_data_files(root):
        try:
            got = load_file(path)
        except Exception as exc:
            if verbose:
                print(f"  [跳过] {path.name}: {exc}")
            skipped.append((path.name, str(exc)[:60]))
            continue
        # 用相对路径当来源，避免子目录里的同名文件（如两个 README.md）混淆
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        for d in got or []:
            d.setdefault("metadata", {})["source"] = rel
        if verbose:
            print(f"  {rel:<40} -> {len(got):>4} 个 Document")
        docs.extend(got)
    if verbose and skipped:
        print(f"  另有 {len(skipped)} 个文件解析失败被跳过")
    return docs


def clean_text(text: str) -> str:
    """基础清洗：压缩空行、去掉孤立空白、统一换行。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
