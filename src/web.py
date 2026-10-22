# -*- coding: utf-8 -*-
"""本地网页服务：知识库问答 + API 配置中心（只用标准库）。

用法：
    python web.py                     # http://127.0.0.1:8000
    python web.py --port 8080
    python web.py --open /config      # 启动后自动打开配置页

页面：
    /         知识库问答（默认首页）
    /config   API 配置（表格 + 弹窗）

接口：
    GET    /api/stats                     索引与模型状态
    GET    /api/files                     data/ 里的资料清单
    POST   /api/ask                       提问
    POST   /api/upload?name=相对路径      上传一个文件（?index=0 只存不建库）
    POST   /api/import_folder             导入本机一个文件夹（{"path": "...", "copy": false}）
    GET    /api/profiles                  配置列表（Key 打码）
    POST   /api/profiles                  新增
    PUT    /api/profiles/{id}             修改
    DELETE /api/profiles/{id}             删除
    POST   /api/profiles/{id}/activate    启用
    POST   /api/profiles/{id}/test        连通性测试
    POST   /api/reindex                   重建索引
    GET/POST /api/selftest_result         仅开发用：浏览器自测结果
"""
from __future__ import annotations

import argparse
import errno
import json
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from ragkb import access, chats, profiles, skips, sources
from ragkb.config import (
    DATA_DIR,
    TOP_K,
    embedding_hint,
    embedding_warning,
    ensure_dirs,
    llm_config,
    setup_stdio,
)
from ragkb.loaders import (
    MAX_FILE_MB,
    MAX_TEXT_MB,
    SKIP_NAME_HINTS,
    SKIP_SUFFIXES,
    SUPPORTED,
    is_ingestible,
)
from ragkb.pipeline import build_index
from ragkb.rag import RAGKB
from ui import (
    CONFIG_SELFTEST,
    PAGE_ASK,
    PAGE_CONFIG,
    PAGE_LIBRARY,
    PAGE_LOGIN,
    SHARED_CSS,
    TOAST,
    UPLOAD_SELFTEST,
)

MAX_UPLOAD_MB = 80

_REINDEX_LOCK = threading.Lock()
_SELFTEST = {"result": None}     # 供 tools/test_*.py 取回浏览器内自测结果
_STORE_STAMP = {"t": 0.0}        # 索引文件时间戳，用于感知外部（watch 模式）写入


def _fill(page: str) -> bytes:
    """把共享样式、通用脚本和页面级自检脚本塞进模板。"""
    html = (page
            .replace("__CSS__", SHARED_CSS)
            .replace("__TOAST__", TOAST)
            .replace("__UPLOAD_SELFTEST__", UPLOAD_SELFTEST))
    return html.encode("utf-8")


def _list_data_files() -> list[dict]:
    """data/ 目录里的资料清单（含子目录），给网页侧栏显示。"""
    out: list[dict] = []
    if not DATA_DIR.exists():
        return out
    for p in sorted(DATA_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUPPORTED or p.name.startswith(("~$", ".")):
            continue
        st = p.stat()
        out.append({
            "name": p.relative_to(DATA_DIR).as_posix(),
            "kb": round(st.st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return out


def _safe_parts(raw: str) -> list[str]:
    """把上传时的相对路径切成安全片段，防目录穿越。"""
    rel = Path(str(raw).replace("\\", "/"))
    return [p for p in rel.parts if p not in ("", ".", "..")]


def _reject_reason(name: str, size_bytes: int) -> str:
    """上传前的过滤：日志、校验清单、超大文本一律不进库。返回拒绝原因。"""
    suffix = Path(name).suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return f"{suffix} 是日志/临时文件"
    if any(h in name.lower() for h in SKIP_NAME_HINTS):
        return "疑似校验清单（md5/checksum）"
    mb = size_bytes / 1048576
    if mb > MAX_FILE_MB:
        return f"{mb:.0f}MB 超过 {MAX_FILE_MB}MB 上限"
    if suffix in (".txt", ".md", ".markdown", ".csv") and mb > MAX_TEXT_MB:
        return f"纯文本 {mb:.1f}MB，疑似日志"
    return ""


class Handler(BaseHTTPRequestHandler):
    server_version = "RAGKB/1.2"
    kb: RAGKB | None = None

    # ————————————————— 基础工具 —————————————————
    def log_message(self, fmt, *args):
        pass

    def _cors_headers(self):
        """只允许浏览器扩展来源跨域调用；普通网站不给，避免被任意页面读取。"""
        origin = (self.headers.get("Origin") or "").strip()
        if origin.startswith(("chrome-extension://", "moz-extension://", "safari-extension://")):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, data, code: int = 200):
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _err(self, msg: str, code: int = 400):
        self._json({"error": msg}, code)

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def _parts(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        return [p for p in path.split("/") if p]

    # ————————————————— 访问控制 —————————————————
    def _client_is_local(self) -> bool:
        host = (self.client_address[0] if self.client_address else "") or ""
        return host in ("127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1")

    def _token(self) -> str | None:
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            key, _, val = part.strip().partition("=")
            if key == access.COOKIE_NAME:
                return val
        return self.headers.get("X-Access-Token") or None

    def _gate(self, method: str) -> bool:
        """返回 True 表示放行；否则已经写好响应。"""
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/login", "/logout"):
            return True
        token = self._token()
        if access.allow(method, path, is_local=self._client_is_local(), token=token):
            return True
        # 走到这里说明是管理操作且没口令
        msg = "这个操作需要管理员口令（问答模块不用）"
        if path.startswith("/api/"):
            self._err(msg, 401)
        else:
            nxt = path + (("?" + urlparse(self.path).query) if urlparse(self.path).query else "")
            self.send_response(302)
            self.send_header("Location", f"/login?next={quote(nxt, safe='')}")
            self.send_header("Content-Length", "0")
            self.end_headers()
        return False

    def _serve_login(self, error: str = ""):
        html = PAGE_LOGIN.replace("__ERROR__", error or "")
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _login(self, password: str) -> bool:
        if not access.verify_password(password):
            return False
        token = access.issue_token()
        days = int(access.config().get("ttl_days") or 7)
        nxt = (parse_qs(urlparse(self.path).query).get("next") or ["/"])[0] or "/"
        if not nxt.startswith("/"):
            nxt = "/"
        body = '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/">'
        self.send_response(302)
        self.send_header("Location", nxt)
        self.send_header("Set-Cookie",
                         f"{access.COOKIE_NAME}={token}; Path=/; Max-Age={days*86400}; "
                         "HttpOnly; SameSite=Lax")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        try:
            self.wfile.write(body.encode())
        except Exception:
            pass
        return True

    def _refresh(self):
        """配置或索引变更后重新加载知识库（嵌入函数可能已改变）。"""
        try:
            self.kb.reload()
        except Exception:
            pass

    def _maybe_reload(self):
        """索引被别的进程改过（watch 自动同步）就重新加载，保证 BM25 索引是新的。"""
        try:
            mtime = self.kb.store.embedder_file.stat().st_mtime
        except Exception:
            return
        if mtime > _STORE_STAMP["t"]:
            _STORE_STAMP["t"] = mtime
            self._refresh()

    def _rebuild(self) -> dict:
        """清空索引内容后全量重建（网页里 kb 开着 Chroma，不能删目录）。"""
        try:
            self.kb.store.reset_contents()
        except Exception:
            pass
        result = build_index(reset=False, verbose=False)
        self._refresh()
        return result

    def _library_payload(self) -> dict:
        """资料库视图：data 文件 + 外部文件夹 + 索引残留，都带上分块统计。"""
        chunks = self.kb.store.all_chunks()
        per_source: dict[str, dict] = {}
        for c in chunks:
            src = str((c.get("metadata") or {}).get("source") or "?")
            d = per_source.setdefault(src, {"chunks": 0, "chars": 0})
            d["chunks"] += 1
            d["chars"] += len(c.get("page_content") or "")

        items: list[dict] = []
        data_files = _list_data_files()
        for f in data_files:
            st = per_source.get(f["name"], {"chunks": 0, "chars": 0})
            ok, reason = is_ingestible(DATA_DIR / f["name"].replace("/", "\\"))
            items.append({
                "name": f["name"], "kind": "data", "size_kb": f["kb"], "mtime": f["mtime"],
                "chunks": st["chunks"], "chars": st["chars"],
                "ext": Path(f["name"]).suffix.lstrip(".").lower(),
                "skip_reason": "" if ok else reason,
            })

        ext_list = sources.list_external()
        ext_prefixes: list[str] = []
        for ext in ext_list:
            prefix = ext["name"] + "/"
            ext_prefixes.append(prefix)
            agg = {"chunks": 0, "chars": 0}
            for src, d in per_source.items():
                if src.startswith(prefix):
                    agg["chunks"] += d["chunks"]
                    agg["chars"] += d["chars"]
            items.append({
                "name": ext["path"], "display": ext["name"], "kind": "external",
                "size_kb": 0, "mtime": ext.get("added_at", ""),
                "chunks": agg["chunks"], "chars": agg["chars"],
                "file_count": ext.get("file_count", 0), "ext": "外部目录",
            })

        known = {i["name"] for i in items if i["kind"] == "data"}
        for src, d in sorted(per_source.items()):
            if src in known or any(src.startswith(p) for p in ext_prefixes):
                continue
            # 索引里有、但文件已经不在 data 也不在外部登记（历史残留，重建会清掉）
            items.append({
                "name": src, "kind": "orphan", "size_kb": 0, "mtime": "",
                "chunks": d["chunks"], "chars": d["chars"], "ext": "残留",
            })

        return {
            "items": items,
            "totals": {
                "files": len([i for i in items if i["kind"] == "data"]),
                "external": len(ext_list),
                "chunks": len(chunks),
                "chars": sum(len(c.get("page_content") or "") for c in chunks),
            },
            "index": self._stats_payload(),
        }

    # ————————————————— 状态 —————————————————
    def _stats_payload(self) -> dict:
        self._maybe_reload()
        stats = self.kb.store.stats()
        cfg = llm_config()
        built = stats.get("built_embedder") or ""
        current = stats.get("embedder") or ""
        return {
            "count": stats["count"],
            "files": stats["files"],
            "backend": stats["backend"],
            "embedder": embedding_hint(),
            "embedder_raw": current,
            "built_embedder": built,
            "embedding_warning": embedding_warning(),
            "embedder_mismatch": bool(built and current and built != current),
            "llm": cfg[2] if cfg else "",
        }

    # ————————————————— GET —————————————————
    def do_GET(self):
        parts = self._parts()
        try:
            if parts == ["login"]:
                self._serve_login()
                return
            if parts == ["logout"]:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.send_header("Set-Cookie",
                                 f"{access.COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if not self._gate("GET"):
                return
            if parts == [] or parts == ["index.html"]:
                self._send(200, _fill(PAGE_ASK), "text/html; charset=utf-8")
                return
            if parts == ["config"]:
                page = PAGE_CONFIG
                if "selftest=" in (urlparse(self.path).query or ""):
                    page = page.replace("</body>", CONFIG_SELFTEST + "</body>")
                self._send(200, _fill(page), "text/html; charset=utf-8")
                return
            if parts == ["library"]:
                self._send(200, _fill(PAGE_LIBRARY), "text/html; charset=utf-8")
                return
            if parts == ["api", "library"]:
                self._json(self._library_payload())
                return
            if parts == ["api", "preview"]:
                qs = parse_qs(urlparse(self.path).query)
                src = (qs.get("source") or [""])[0]
                limit = int((qs.get("limit") or ["6"])[0])
                prefix_mode = src.endswith("/")
                out = []
                for c in self.kb.store.all_chunks():
                    meta = c.get("metadata") or {}
                    s = str(meta.get("source") or "")
                    hit = s.startswith(src) if prefix_mode else s == src
                    if not hit:
                        continue
                    out.append({
                        "source": s,
                        "page": meta.get("page"),
                        "row": meta.get("row"),
                        "chars": len(c.get("page_content") or ""),
                        "text": (c.get("page_content") or "")[:600],
                    })
                    if len(out) >= limit:
                        break
                self._json({"source": src, "chunks": out})
                return
            if parts == ["api", "chats"]:
                self._json({"chats": chats.list_chats()})
                return
            if len(parts) == 3 and parts[:2] == ["api", "chats"]:
                chat = chats.get_chat(parts[2])
                if chat is None:
                    self._err("对话不存在", 404)
                    return
                self._json({"chat": chat})
                return
            if parts == ["api", "skips"]:
                self._json({"skips": skips.recent(20)})
                return
            if parts == ["api", "whoami"]:
                local = self._client_is_local()
                admin = local or access.token_ok(self._token() or "") or not access.enabled()
                self._json({
                    "admin": bool(admin),
                    "local": bool(local),
                    "enabled": access.enabled(),
                    "label": "本机管理员" if local else ("管理员" if admin else "访客"),
                })
                return
            if parts == ["api", "access"]:
                self._json(access.snapshot())
                return
            if parts == ["api", "stats"]:
                self._json(self._stats_payload())
                return
            if parts == ["api", "files"]:
                self._json({"files": _list_data_files()})
                return
            if parts == ["api", "selftest_result"]:
                self._json(_SELFTEST["result"] or {"items": []})
                return
            if parts == ["api", "profiles"]:
                self._json({
                    "profiles": profiles.list_profiles(),
                    "providers": profiles.PROVIDERS,
                    "embeddings": profiles.EMBEDDING_MODES,
                    "active_id": (profiles.active_profile() or {}).get("id", ""),
                    "stats": self._stats_payload(),
                })
                return
            self._err("接口不存在", 404)
        except Exception as exc:
            self._err(f"{type(exc).__name__}: {exc}", 500)

    # ————————————————— POST —————————————————
    def do_POST(self):
        parts = self._parts()
        try:
            if parts == ["login"]:
                raw = b""
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                    raw = self.rfile.read(length) if length else b""
                except Exception:
                    raw = b""
                fields = parse_qs(raw.decode("utf-8", "replace"))
                password = (fields.get("password") or [""])[0]
                ip = (self.client_address[0] if self.client_address else "") or "?"
                blocked, wait = access.login_blocked(ip)
                if blocked:
                    self._send(429,
                               PAGE_LOGIN.replace(
                                   "__ERROR__",
                                   f"尝试次数过多，请 {wait} 秒后再试").encode("utf-8"),
                               "text/html; charset=utf-8")
                    return
                if not self._login(password):
                    access.record_failure(ip)
                    self._serve_login("口令不对，请再试一次")
                else:
                    access.clear_failures(ip)
                return
            if not self._gate("POST"):
                return
            if parts == ["api", "ask"]:
                self._maybe_reload()
                data = self._body()
                question = (data.get("question") or "").strip()
                k = int(data.get("k") or TOP_K)
                use_llm = bool(data.get("use_llm", True))
                result = self.kb.ask(question, top_k=k, use_llm=use_llm)
                self._json({
                    "question": result["question"],
                    "answer": result["answer"],
                    "mode": result["mode"],
                    "note": result.get("note", ""),
                    "sources": [
                        {
                            "index": s["index"], "source": s["source"], "page": s.get("page"),
                            "row": s.get("row"), "sheet": s.get("sheet"),
                            "score": s["score"], "snippet": s["snippet"],
                        }
                        for s in result.get("sources", [])
                    ],
                })
                return

            if parts == ["api", "upload"]:
                self._handle_upload()
                return

            if parts == ["api", "import_folder"]:
                self._handle_import_folder()
                return

            if parts == ["api", "external_remove"]:
                payload = self._body()
                target = (payload.get("path") or "").strip()
                if not target:
                    self._err("缺少路径")
                    return
                if not sources.remove_external(target):
                    self._err("这个外部文件夹没有登记过", 404)
                    return
                if not _REINDEX_LOCK.acquire(timeout=120):
                    self._err("正在建库，请稍后重试", 409)
                    return
                try:
                    result = self._rebuild()
                finally:
                    _REINDEX_LOCK.release()
                self._json({"ok": True, "chunks": result.get("chunks", 0),
                            "count": result.get("stats", {}).get("count", 0)})
                return

            if parts == ["api", "selftest_result"]:
                _SELFTEST["result"] = self._body()
                self._json({"ok": True})
                return

            if parts == ["api", "access"]:
                self._json({"ok": True, **access.update(self._body())})
                return
            if parts == ["api", "search"]:
                # 只检索不生成：给外部 Agent 当工具用
                self._maybe_reload()
                data = self._body()
                query = (data.get("query") or data.get("question") or "").strip()
                k = int(data.get("k") or TOP_K)
                if not query:
                    self._err("缺少 query")
                    return
                hits = self.kb.retrieve(query, top_k=k)
                self._json({
                    "query": query,
                    "hits": [
                        {
                            "index": i,
                            "source": h["metadata"].get("source", "?"),
                            "page": h["metadata"].get("page"),
                            "row": h["metadata"].get("row"),
                            "score": h["score"],
                            "content": h["content"],
                        }
                        for i, h in enumerate(hits, 1)
                    ],
                })
                return

            if parts == ["api", "chats"]:
                payload = self._body()
                chat = chats.create_chat(payload.get("title") or "")
                self._json({"ok": True, "chat": chat}, 201)
                return

            if len(parts) == 4 and parts[:2] == ["api", "chats"] and parts[3] == "messages":
                payload = self._body()
                chat = chats.append_message(
                    parts[2],
                    payload.get("role") or "me",
                    payload.get("content") or "",
                    mode=payload.get("mode"),
                    note=payload.get("note"),
                    sources=payload.get("sources"),
                )
                if chat is None:
                    self._err("对话不存在", 404)
                    return
                self._json({"ok": True, "chat": chats.summary(chat)})
                return

            if parts == ["api", "profiles"]:
                payload = self._body()
                if not (payload.get("base_url") or "").strip() or not (payload.get("model") or "").strip():
                    self._err("Base URL 和模型名必须填写")
                    return
                prof = profiles.create_profile(payload)
                self._refresh()
                self._json({"ok": True, "profile": prof}, 201)
                return

            if len(parts) == 4 and parts[:2] == ["api", "profiles"] and parts[3] == "activate":
                if not profiles.activate_profile(parts[2]):
                    self._err("配置不存在", 404)
                    return
                self._refresh()
                self._json({"ok": True, "stats": self._stats_payload()})
                return

            if len(parts) == 4 and parts[:2] == ["api", "profiles"] and parts[3] == "test":
                result = profiles.test_profile(parts[2])
                self._refresh()
                self._json(result)
                return

            if parts == ["api", "reindex"]:
                if not _REINDEX_LOCK.acquire(timeout=5):
                    self._err("已有重建任务在进行中", 409)
                    return
                try:
                    result = self._rebuild()
                finally:
                    _REINDEX_LOCK.release()
                if not result.get("ok"):
                    self._err(result.get("error", "重建失败"), 500)
                    return
                self._json({
                    "ok": True,
                    "chunks": result["chunks"],
                    "files": result["files"],
                    "backend": result["backend"],
                    "embedder": result["embedder"],
                })
                return

            self._err("接口不存在", 404)
        except Exception as exc:
            self._err(f"{type(exc).__name__}: {exc}", 500)

    # ————————————————— PUT / DELETE —————————————————
    def do_PUT(self):
        parts = self._parts()
        try:
            if not self._gate("PUT"):
                return
            if len(parts) == 3 and parts[:2] == ["api", "chats"]:
                payload = self._body()
                chat = chats.rename_chat(parts[2], payload.get("title") or "")
                if chat is None:
                    self._err("对话不存在", 404)
                    return
                self._json({"ok": True, "chat": chats.summary(chat)})
                return
            if len(parts) == 3 and parts[:2] == ["api", "profiles"]:
                prof = profiles.update_profile(parts[2], self._body())
                if not prof:
                    self._err("配置不存在", 404)
                    return
                self._refresh()
                self._json({"ok": True, "profile": prof})
                return
            self._err("接口不存在", 404)
        except Exception as exc:
            self._err(f"{type(exc).__name__}: {exc}", 500)

    def do_DELETE(self):
        parts = self._parts()
        try:
            if not self._gate("DELETE"):
                return
            if len(parts) == 3 and parts[:2] == ["api", "chats"]:
                if not chats.delete_chat(parts[2]):
                    self._err("对话不存在", 404)
                    return
                self._json({"ok": True})
                return
            if parts == ["api", "skips"]:
                skips.clear()
                self._json({"ok": True})
                return
            if parts == ["api", "files"]:
                self._handle_delete_file()
                return
            if len(parts) == 3 and parts[:2] == ["api", "profiles"]:
                if not profiles.delete_profile(parts[2]):
                    self._err("配置不存在", 404)
                    return
                self._refresh()
                self._json({"ok": True})
                return
            self._err("接口不存在", 404)
        except Exception as exc:
            self._err(f"{type(exc).__name__}: {exc}", 500)

    # ————————————————— 上传 / 导入文件夹 —————————————————
    def _handle_upload(self):
        """网页上传：body 是文件原始字节，相对路径放在 ?name= 里。

        ?index=0 表示只存文件、稍后统一建库（整个文件夹批量上传时用）。
        不走 multipart，解析简单、失败率低；前端一个文件发一次请求。
        """
        qs = parse_qs(urlparse(self.path).query)
        raw_name = (qs.get("name") or [""])[0]
        do_index = (qs.get("index") or ["1"])[0] not in ("0", "false", "no")

        parts = _safe_parts(raw_name)
        if not parts:
            self._err("缺少文件名")
            return
        suffix = Path(parts[-1]).suffix.lower()
        if suffix in SKIP_SUFFIXES:
            self._err(f"{parts[-1]} 已跳过：{suffix} 是日志/临时文件")
            return
        if suffix not in SUPPORTED:
            self._err(f"不支持的格式 {suffix or '(无扩展名)'}，"
                      f"支持：{'、'.join(sorted(s.lstrip('.') for s in SUPPORTED))}")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._err("文件内容为空")
            return
        if length > MAX_UPLOAD_MB * 1024 * 1024:
            self._err(f"文件超过 {MAX_UPLOAD_MB}MB，请拆分后再传")
            return

        reason = _reject_reason(parts[-1], length)
        if reason:
            skips.record("/".join(parts), reason)
            self._err(f"{parts[-1]} 已跳过：{reason}")
            return

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        target = DATA_DIR.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.rfile.read(length)
        target.write_bytes(payload)

        if not do_index:
            self._json({"ok": True, "name": "/".join(parts),
                        "size_kb": round(len(payload) / 1024, 1), "queued": True})
            return

        if not _REINDEX_LOCK.acquire(timeout=60):
            self._err("正在处理另一个建库任务，请稍后重试", 409)
            return
        try:
            result = build_index(files=[target], verbose=False)
        finally:
            _REINDEX_LOCK.release()

        self._refresh()
        if not result.get("ok"):
            self._err(result.get("error", "入库失败"), 500)
            return
        stats = result["stats"]
        self._json({
            "ok": True,
            "name": "/".join(parts),
            "size_kb": round(len(payload) / 1024, 1),
            "chunks": result["chunks"],
            "count": stats["count"],
            "files": stats["files"],
        })

    def _handle_import_folder(self):
        """导入本机任意位置的一个文件夹：默认直接读原位置，不复制。"""
        data = self._body()
        raw = (data.get("path") or "").strip().strip('"')
        copy_mode = bool(data.get("copy"))
        if not raw:
            self._err("请填写文件夹路径")
            return

        src = Path(raw).expanduser()
        if not src.exists() or not src.is_dir():
            self._err(f"文件夹不存在：{raw}")
            return

        targets: list[tuple[Path, str]] = []
        skipped: list[str] = []
        for p in sorted(src.rglob("*")):
            if not p.is_file():
                continue
            if p.name.startswith(("~$", ".")):
                continue
            ok, reason = is_ingestible(p)
            if not ok:
                skipped.append(f"{p.name}（{reason}）")
                continue
            targets.append((p, f"{src.name}/{p.relative_to(src).as_posix()}"))

        if not targets:
            tip = f"，跳过 {len(skipped)} 个" if skipped else ""
            self._err(f"这个文件夹里没有可解析的文件（支持 "
                      f"{'、'.join(sorted(s.lstrip('.') for s in SUPPORTED))}）{tip}")
            return

        if copy_mode:
            dest_root = DATA_DIR / src.name
            for p, label in targets:
                rel = Path(label).relative_to(src.name)
                dst = dest_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
            files_param = [Path(t[0]) for t in targets]
        else:
            files_param = targets          # (path, label)：直接读原位置

        if not _REINDEX_LOCK.acquire(timeout=300):
            self._err("正在处理另一个建库任务，请稍后重试", 409)
            return
        try:
            result = build_index(files=files_param, verbose=False)
        finally:
            _REINDEX_LOCK.release()

        self._refresh()
        if not result.get("ok"):
            self._err(result.get("error", "入库失败"), 500)
            return
        if not copy_mode:
            # 登记外部目录，保证以后重建索引时还能读到（不复制文件）
            try:
                sources.add_external(src)
            except Exception:
                pass
        stats = result["stats"]
        self._json({
            "ok": True,
            "folder": src.name,
            "copied": copy_mode,
            "file_count": len(targets),
            "skipped_count": len(skipped),
            "skipped": skipped[:8],
            "chunks": result["chunks"],
            "count": stats["count"],
            "files": len(stats["files"]),
            "sample": [t[1] for t in targets[:5]],
        })

    def _handle_delete_file(self):
        """删除 data/ 里的一个资料，并把它的索引块一起清掉（整库重建）。"""
        qs = parse_qs(urlparse(self.path).query)
        raw = (qs.get("name") or [""])[0]
        parts = _safe_parts(raw)
        if not parts:
            self._err("缺少文件名")
            return
        target = DATA_DIR.joinpath(*parts)
        try:
            target.resolve().relative_to(DATA_DIR.resolve())
        except Exception:
            self._err("路径不合法")
            return
        if not target.exists():
            self._err(f"文件不存在：{raw}")
            return
        try:
            target.unlink()
        except Exception as exc:
            self._err(f"删除失败：{exc}", 500)
            return

        # 顺手清理空目录
        parent = target.parent
        while parent != DATA_DIR and parent.exists():
            try:
                next(parent.iterdir())
                break
            except StopIteration:
                parent.rmdir()
                parent = parent.parent
            except Exception:
                break

        if not _REINDEX_LOCK.acquire(timeout=120):
            self._err("正在建库，请稍后重试", 409)
            return
        try:
            result = self._rebuild()
        finally:
            _REINDEX_LOCK.release()
        self._json({
            "ok": True,
            "deleted": "/".join(parts),
            "chunks": result.get("chunks", 0),
            "count": result.get("stats", {}).get("count", 0),
        })


def _port_in_use(port: int) -> bool:
    """端口上是否已有服务在响应。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0



def _maybe_start_local_model() -> None:
    """如果当前启用的档案是本地模型（ollama），启动前把它拉起来；用云端则什么都不做。"""
    try:
        from ragkb.profiles import active_profile

        provider = (active_profile() or {}).get("provider", "").lower()
    except Exception:
        return
    if provider != "ollama":
        return
    script = Path(__file__).resolve().parent / "tools" / "ensure_ollama.py"
    if not script.exists():
        return
    print("  [本地模型] 正在按需启动 Ollama…", flush=True)
    try:
        subprocess.run([sys.executable, str(script)], timeout=120)
    except Exception as exc:
        print(f"  [本地模型] 启动失败：{exc}（问答时可能退回离线抽取）", flush=True)


def main() -> int:
    setup_stdio()
    ensure_dirs()
    parser = argparse.ArgumentParser(description="RAG 知识库网页版（问答 + API 配置）")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1",
                        help="默认只监听本机；填 0.0.0.0 可让同一局域网的设备访问")
    parser.add_argument("--open", nargs="?", const="/", default=None,
                        help="启动后自动打开浏览器，可带路径（如 --open /config）")
    args = parser.parse_args()

    profiles.ensure_default_profile()

    # Windows 的 SO_REUSEADDR 允许两个进程绑同一端口，必须先探测再绑
    if _port_in_use(args.port):
        print("=" * 68)
        print(f"  端口 {args.port} 上已经有服务在运行，本次不重复启动。")
        print("  直接给你打开已有那个服务的页面：")
        print(f"      http://127.0.0.1:{args.port}/")
        print(f"      http://127.0.0.1:{args.port}/config")
        print("  想另开一份： python web.py --port 8080")
        print("=" * 68)
        if args.open is not None:
            path = args.open if str(args.open).startswith("/") else "/"
            webbrowser.open(f"http://127.0.0.1:{args.port}{path}")
        return 0

    Handler.kb = RAGKB()
    stats = Handler.kb.store.stats()
    try:
        _STORE_STAMP["t"] = Handler.kb.store.embedder_file.stat().st_mtime
    except Exception:
        pass
    if not stats["exists"]:
        print("[提示] 索引为空，请先运行： python ingest.py")

    _maybe_start_local_model()

    class ServerV4(ThreadingHTTPServer):
        address_family = socket.AF_INET
        daemon_threads = True

    class ServerV6(ThreadingHTTPServer):
        address_family = socket.AF_INET6
        daemon_threads = True

    servers: list[ThreadingHTTPServer] = []
    busy_codes = {errno.EADDRINUSE}
    if hasattr(errno, "WSAEADDRINUSE"):
        busy_codes.add(errno.WSAEADDRINUSE)

    try:
        servers.append(ServerV4((args.host, args.port), Handler))
    except OSError as exc:
        if exc.errno in busy_codes:
            print("=" * 68)
            print(f"  端口 {args.port} 已被占用，本次没有启动新服务。")
            print(f"  已有服务的话，直接打开： http://127.0.0.1:{args.port}/")
            print("=" * 68)
            return 1
        raise

    # 同时监听 IPv6 回环，避免浏览器访问 localhost 时先走 ::1 连不上
    if args.host in ("127.0.0.1", "localhost", "::1"):
        try:
            servers.append(ServerV6(("::1", args.port), Handler))
        except OSError:
            pass

    cfg = llm_config()
    active = profiles.active_profile()
    print("=" * 68)
    print("  RAG 知识库 · 网页版")
    print(f"  问答页   : http://127.0.0.1:{args.port}/")
    print(f"  API 配置 : http://127.0.0.1:{args.port}/config")
    if len(servers) > 1:
        print(f"            http://localhost:{args.port}/  也可访问（IPv6 已监听）")
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"  监听地址 : {args.host}（局域网设备可用本机 IP 访问）")
    print(f"  索引     : {stats['count']} 块 / {len(stats['files'])} 文件（{stats['backend']}）")
    print(f"  嵌入模型 : {embedding_hint()}")
    print(f"  对话模型 : {cfg[2] if cfg else '未配置（离线抽取式回答）'}")
    print(f"  配置档案 : {active['name'] if active else '无'}（共 {len(profiles.list_profiles())} 套）")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        lan_ip = ""
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            lan_ip = probe.getsockname()[0]
            probe.close()
        except Exception:
            try:
                lan_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                lan_ip = ""
        acfg = access.config()
        if lan_ip and not lan_ip.startswith("127."):
            print(f"  给别人用 : http://{lan_ip}:{args.port}/")
        if acfg.get("enabled"):
            print(f"  访问口令 : {acfg.get('password')}（外人首次访问需输入）")
            print("             改口令：改 config\\access.json 或用 service_task.py 重启后重新生成")
        else:
            print("  访问控制 : 已关闭（任何拿到地址的人都能用，含删除资料）")
    print("  停止服务 : Ctrl+C")
    print("=" * 68)

    if args.open is not None:
        path = args.open if str(args.open).startswith("/") else "/"
        url = f"http://127.0.0.1:{args.port}{path}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    for extra in servers[1:]:
        threading.Thread(target=extra.serve_forever, daemon=True).start()

    try:
        servers[0].serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        for s in servers:
            try:
                s.server_close()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
