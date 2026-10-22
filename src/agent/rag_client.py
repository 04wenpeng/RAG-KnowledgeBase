# -*- coding: utf-8 -*-
"""RAG 知识库的 Python 客户端（纯标准库，任何 agent 都能 import 或命令行调用）。

用法一：当模块用
    from rag_client import RAGClient
    kb = RAGClient()                       # 默认 http://127.0.0.1:8000
    kb.ask("什么是向量数据库？")            # 检索 + 生成，返回 dict
    kb.search("向量数据库", k=3)            # 只检索，返回片段列表

用法二：当命令行用
    python agent/rag_client.py "什么是向量数据库？"
    python agent/rag_client.py --search "chunk_size"
    python agent/rag_client.py --health
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# 默认地址可用环境变量覆盖：别的电脑上设 RAG_KB_URL=http://<知识库那台机>:8000
DEFAULT_BASE = os.environ.get("RAG_KB_URL", "http://127.0.0.1:8000").rstrip("/")


class RAGClient:
    def __init__(self, base_url: str = DEFAULT_BASE, timeout: int = 120,
                 admin_password: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # 只读能力（ask / search / health）不需要口令；
        # 写操作（上传资料）需要管理员口令，传了才会自动登录。
        self.admin_password = admin_password
        self._cookie: str | None = None

    # ——————— 底层请求 ———————
    def _request(self, method: str, path: str, payload=None, raw: bytes | None = None,
                 content_type: str = "application/json") -> dict:
        data = raw if raw is not None else (
            json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None)
        headers = {}
        if data is not None:
            headers["Content-Type"] = content_type
        if self._cookie:
            headers["Cookie"] = self._cookie
        req = urllib.request.Request(self.base_url + path, data=data,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", "replace")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            try:
                msg = json.loads(detail).get("error", detail)
            except Exception:
                msg = detail
            raise RuntimeError(f"知识库返回 HTTP {exc.code}：{msg}") from None
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"连不上知识库 {self.base_url}（{{}}）。先启动：python web.py".format(exc.reason)
            ) from None

    # ——————— 管理员登录（写操作用）———————
    def login(self, password: str | None = None) -> str:
        """用管理员口令换一个会话 cookie；写操作会自动调用。"""
        pw = password or self.admin_password
        if not pw:
            raise RuntimeError(
                "这个操作需要管理员口令。构造时传 RAGClient(admin_password='...')，"
                "或显式调用 kb.login('口令')。")
        data = urllib.parse.urlencode({"password": pw}).encode("utf-8")

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None

        req = urllib.request.Request(
            self.base_url + "/login", data=data, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            resp = urllib.request.build_opener(_NoRedirect).open(req, timeout=self.timeout)
            set_cookie = resp.headers.get("Set-Cookie") or ""
        except urllib.error.HTTPError as exc:      # 302 正常也是 HTTPError
            set_cookie = exc.headers.get("Set-Cookie") or ""
            if exc.code not in (301, 302):
                raise RuntimeError(f"登录失败（HTTP {exc.code}）") from None
        cookie = set_cookie.split(";")[0]
        if not cookie:
            raise RuntimeError("登录失败：口令不对？")
        self._cookie = cookie
        return cookie

    def whoami(self) -> dict:
        return self._request("GET", "/api/whoami")

    # ——————— 三个能力 ———————
    def health(self) -> dict:
        return self._request("GET", "/api/stats")

    def search(self, query: str, k: int = 4) -> list[dict]:
        """只检索，返回命中的文档片段（适合 agent 自己组织答案）。"""
        data = self._request("POST", "/api/search", {"query": query, "k": k})
        return data.get("hits", [])

    def ask(self, question: str, k: int = 4, use_llm: bool = True) -> dict:
        """检索 + 生成，返回 {answer, mode, sources, note}。"""
        return self._request("POST", "/api/ask",
                             {"question": question, "k": k, "use_llm": use_llm})

    def add_document(self, path: str | Path) -> dict:
        """往知识库加一个文件（需要管理员口令，会自动登录）。"""
        p = Path(path)
        if not self._cookie:
            self.login()
        name = urllib.request.quote(p.name)
        return self._request("POST", f"/api/upload?name={name}", raw=p.read_bytes(),
                             content_type="application/octet-stream")

    def sources_text(self, result: dict, limit: int = 3) -> str:
        """把出处整理成一行行文本，方便塞进 agent 的上下文。"""
        lines = []
        for s in (result.get("sources") or [])[:limit]:
            loc = f"第{s['page']}页" if s.get("page") else (s.get("source") or "")
            lines.append(f"- {s.get('source')} {loc}（相关度 {s.get('score')}）")
        return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG 知识库命令行客户端")
    parser.add_argument("text", nargs="*", help="问题或检索词")
    parser.add_argument("--base", default=DEFAULT_BASE, help="知识库地址")
    parser.add_argument("--search", action="store_true", help="只检索，不生成")
    parser.add_argument("--health", action="store_true", help="只看服务状态")
    parser.add_argument("-k", "--top-k", type=int, default=4)
    args = parser.parse_args()

    kb = RAGClient(args.base)
    try:
        if args.health:
            print(json.dumps(kb.health(), ensure_ascii=False, indent=2))
            return 0
        text = " ".join(args.text).strip()
        if not text:
            print("用法：python agent/rag_client.py \"你的问题\"")
            return 1
        if args.search:
            for hit in kb.search(text, k=args.top_k):
                print(f"[{hit['index']}] {hit['source']} "
                      f"{('第' + str(hit['page']) + '页') if hit.get('page') else ''} "
                      f"score={hit['score']}")
                print("   ", hit["content"][:160].replace("\n", " "), "…")
            return 0
        result = kb.ask(text, k=args.top_k)
        print(f"模式：{result.get('mode')}")
        print(result.get("answer"))
        if result.get("sources"):
            print("\n出处：")
            print(kb.sources_text(result, limit=len(result["sources"])))
        return 0
    except RuntimeError as exc:
        print(f"[错误] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
