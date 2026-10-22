# -*- coding: utf-8 -*-
"""记录"哪些文件被跳过、为什么"，让过滤不再是黑盒。

写 config/ingest.log（每行一条 JSON），网页资料库页会展示最近若干条——
这样"我明明放进去了怎么没入库"能自己看出来原因。
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR

LOG_FILE = BASE_DIR / "config" / "ingest.log"
_LOCK = threading.Lock()
_MAX_KEEP = 200


def record(name: str, reason: str) -> None:
    """记一条跳过记录（同名同原因只保留最新一条，避免刷屏）。"""
    item = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": str(name),
        "reason": str(reason),
    }
    with _LOCK:
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            lines = []
            if LOG_FILE.exists():
                lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            rows = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("name") == item["name"]:
                    continue          # 去掉同名旧记录
                rows.append(obj)
            rows.append(item)
            rows = rows[-_MAX_KEEP:]
            LOG_FILE.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass


def recent(limit: int = 20) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    out = []
    try:
        for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        return []
    return list(reversed(out))[:limit]


def clear() -> None:
    with _LOCK:
        try:
            if LOG_FILE.exists():
                LOG_FILE.unlink()
        except Exception:
            pass
