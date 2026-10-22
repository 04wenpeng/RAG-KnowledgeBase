# -*- coding: utf-8 -*-
"""外部资料源登记。

"填路径导入文件夹"是直接读原位置、不复制文件的。如果只在索引里加块，
下次重建索引就会凭空消失——所以把这些文件夹登记到
config/external_sources.json，重建时一并读进来。
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR
from .loaders import is_ingestible

CONFIG_DIR = BASE_DIR / "config"
EXTERNAL_FILE = CONFIG_DIR / "external_sources.json"
_LOCK = threading.RLock()


def _read() -> dict:
    if not EXTERNAL_FILE.exists():
        return {"folders": []}
    try:
        data = json.loads(EXTERNAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"folders": []}
    data.setdefault("folders", [])
    return data


def _write(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = EXTERNAL_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(EXTERNAL_FILE)


def list_external() -> list[dict]:
    """已登记的外部文件夹（按路径去重，去掉已不存在的）。"""
    with _LOCK:
        data = _read()
        alive = []
        for item in data["folders"]:
            p = Path(item.get("path", ""))
            if not p.is_dir():
                continue
            files = [f for f in p.rglob("*") if f.is_file() and is_ingestible(f)[0]]
            alive.append({
                "path": str(p),
                "name": p.name,
                "added_at": item.get("added_at", ""),
                "file_count": len(files),
            })
        return alive


def add_external(folder: Path) -> dict:
    folder = Path(folder).expanduser().resolve()
    with _LOCK:
        data = _read()
        for item in data["folders"]:
            if Path(item.get("path", "")).resolve() == folder:
                item["added_at"] = item.get("added_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                _write(data)
                return item
        item = {
            "path": str(folder),
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["folders"].append(item)
        _write(data)
        return item


def remove_external(path: str) -> bool:
    target = Path(str(path)).expanduser()
    with _LOCK:
        data = _read()
        before = len(data["folders"])
        kept = []
        for item in data["folders"]:
            try:
                same = Path(item.get("path", "")).resolve() == target.resolve()
            except Exception:
                same = item.get("path") == str(target)
            if not same:
                kept.append(item)
        if len(kept) == before:
            return False
        data["folders"] = kept
        _write(data)
        return True


def external_files() -> list[tuple[Path, str]]:
    """所有外部文件夹里的可入库文件，返回 [(路径, 来源标签)]。"""
    out: list[tuple[Path, str]] = []
    for item in list_external():
        root = Path(item["path"])
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.name.startswith(("~$", ".")):
                continue
            if not is_ingestible(p)[0]:
                continue
            out.append((p, f"{root.name}/{p.relative_to(root).as_posix()}"))
    return out
