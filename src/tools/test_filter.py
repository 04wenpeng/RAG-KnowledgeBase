# -*- coding: utf-8 -*-
"""测试"噪声文件过滤"与"单个资料删除"。

用法：python tools/test_filter.py 8000
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def call(method, path, payload=None, raw=None, ctype=None):
    data = raw if raw is not None else (
        json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None)
    headers = {"Content-Type": ctype or ("application/json" if payload is not None else "")}
    headers = {k: v for k, v in headers.items() if v}
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


def ok(label, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + label + (f"  {extra}" if extra else ""))
    return bool(cond)


def main() -> int:
    passed = True
    root = Path(tempfile.mkdtemp(prefix="ragkb-noise-")) / "嵌入式资料"
    (root / "文档").mkdir(parents=True, exist_ok=True)
    # 应入库
    (root / "文档" / "笔记.md").write_text("# 笔记\n\nLVGL 是一个开源图形库。\n", encoding="utf-8")
    # 应被过滤：日志 / 校验清单 / 超大文本
    (root / "JLinkLog.txt").write_text("log line\n" * 400000, encoding="utf-8")   # ~3.6MB
    (root / "images_md5.json").write_text('{"a":"b"}', encoding="utf-8")
    (root / "build.log").write_text("compile...\n", encoding="utf-8")

    code, res = call("POST", "/api/import_folder", {"path": str(root), "copy": False})
    passed &= ok("导入成功", code == 200 and res.get("ok"),
                 f"files={res.get('file_count')} skipped={res.get('skipped_count')}")
    passed &= ok("只入库 1 个文件", res.get("file_count") == 1)
    passed &= ok("识别出 3 个噪声文件", res.get("skipped_count") == 3,
                 "；".join(res.get("skipped", [])))
    passed &= ok("跳过的原因写清楚了",
                 any("日志" in s or "校验" in s for s in res.get("skipped", [])))

    # 上传单个 .log 应被拒绝
    code, res2 = call("POST", "/api/upload?name=bad.log", raw=b"x" * 100,
                      ctype="application/octet-stream")
    passed &= ok("单文件上传 .log 被拒绝", code == 400, str(res2.get("error"))[:40])

    # 上传一个正常文件，然后删掉它
    code, up = call("POST", "/api/upload?name=" + urllib.request.quote("临时资料.txt"),
                    raw="临时内容：测试删除。".encode(), ctype="text/plain")
    passed &= ok("正常文件可以上传", code == 200 and up.get("ok"), f"chunks={up.get('chunks')}")

    code, before = call("GET", "/api/stats")
    code, dele = call("DELETE", "/api/files?name=" + urllib.request.quote("临时资料.txt"))
    passed &= ok("DELETE /api/files 成功", code == 200 and dele.get("ok"),
                 f"现有 {dele.get('count')} 块")
    code, after = call("GET", "/api/stats")
    passed &= ok("删除后索引块数减少", after["count"] < before["count"],
                 f"{before['count']} → {after['count']}")
    passed &= ok("文件不再出现在清单里",
                 not any(f["name"] == "临时资料.txt" for f in
                         call("GET", "/api/files")[1]["files"]))

    # 路径穿越应被挡住
    code, res3 = call("DELETE", "/api/files?name=" + urllib.request.quote("../../web.py"))
    passed &= ok("拒绝路径穿越", code in (400, 404), f"HTTP {code}")

    # 注销外部登记（否则会留在 config/external_sources.json 里污染真实配置）
    call("POST", "/api/external_remove", {"path": str(root)})
    shutil.rmtree(root.parent, ignore_errors=True)
    call("POST", "/api/reindex")
    print("\n" + ("过滤与删除都正常 ✅" if passed else "有失败项 ❌"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
