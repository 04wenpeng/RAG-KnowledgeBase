# -*- coding: utf-8 -*-
"""对话存储：每个会话一个 JSON 文件，放在 config/chats/。

结构：
    {"id": "...", "title": "什么是向量数据库", "created_at": "...",
     "updated_at": "...", "messages": [{"role": "me|ai", "content": "...",
     "mode": "llm|extractive", "note": "", "sources": [...], "ts": "..."}]}
"""
from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR

CHAT_DIR = BASE_DIR / "config" / "chats"
_LOCK = threading.RLock()
_TITLE_LEN = 24


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _path(cid: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "", cid or "")
    return CHAT_DIR / f"{safe}.json"


def _read(cid: str) -> dict | None:
    p = _path(cid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write(chat: dict) -> None:
    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(chat["id"])
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(chat, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def list_chats() -> list[dict]:
    """按更新时间倒序列出会话摘要。"""
    out = []
    if not CHAT_DIR.exists():
        return out
    for p in CHAT_DIR.glob("*.json"):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            "id": c.get("id", p.stem),
            "title": c.get("title") or "新对话",
            "updated_at": c.get("updated_at", ""),
            "created_at": c.get("created_at", ""),
            "count": len(c.get("messages") or []),
        })
    out.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return out


def create_chat(title: str = "") -> dict:
    cid = "c_" + uuid.uuid4().hex[:10]
    chat = {
        "id": cid,
        "title": (title or "新对话").strip()[:_TITLE_LEN],
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
    }
    with _LOCK:
        _write(chat)
    return chat


def get_chat(cid: str) -> dict | None:
    return _read(cid)


def append_message(cid: str, role: str, content: str, **extra) -> dict | None:
    """追加一条消息；首条用户消息会自动变成会话标题。"""
    with _LOCK:
        chat = _read(cid)
        if chat is None:
            return None
        msg = {"role": role, "content": (content or "")[:8000], "ts": _now()}
        for k in ("mode", "note", "sources"):
            if extra.get(k) not in (None, "", []):
                msg[k] = extra[k]
        chat.setdefault("messages", []).append(msg)
        if role == "me" and (not chat.get("title") or chat["title"] == "新对话"):
            title = re.sub(r"\s+", " ", content or "").strip()[:_TITLE_LEN]
            if title:
                chat["title"] = title
        chat["updated_at"] = _now()
        _write(chat)
        return chat


def rename_chat(cid: str, title: str) -> dict | None:
    with _LOCK:
        chat = _read(cid)
        if chat is None:
            return None
        chat["title"] = (title or "新对话").strip()[:_TITLE_LEN] or "新对话"
        chat["updated_at"] = _now()
        _write(chat)
        return chat


def delete_chat(cid: str) -> bool:
    with _LOCK:
        p = _path(cid)
        if not p.exists():
            return False
        try:
            p.unlink()
            return True
        except Exception:
            return False


def summary(chat: dict) -> dict:
    return {
        "id": chat.get("id"),
        "title": chat.get("title") or "新对话",
        "updated_at": chat.get("updated_at", ""),
        "created_at": chat.get("created_at", ""),
        "count": len(chat.get("messages") or []),
    }
