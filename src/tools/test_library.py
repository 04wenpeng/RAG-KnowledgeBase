# -*- coding: utf-8 -*-
"""资料库管理测试：列表统计、预览、外部目录登记/删除、重建后仍在。

用法：python tools/test_library.py 8000
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
    headers = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    elif ctype:
        headers["Content-Type"] = ctype
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

    print("1) 资料库列表")
    code, lib = call("GET", "/api/library")
    passed &= ok("GET /api/library", code == 200 and "items" in lib,
                 f"{lib.get('totals', {}).get('files')} 文件 / {lib.get('totals', {}).get('chunks')} 块")
    passed &= ok("每个文件都有分块数", all("chunks" in it for it in lib["items"]))
    passed &= ok("分块总数与索引一致",
                 sum(it["chunks"] for it in lib["items"]) == lib["totals"]["chunks"],
                 f"{sum(it['chunks'] for it in lib['items'])} vs {lib['totals']['chunks']}")

    print("2) 内容预览")
    first = next((it for it in lib["items"] if it["kind"] == "data"), None)
    if first:
        code, pv = call("GET", "/api/preview?limit=2&source=" + urllib.request.quote(first["name"]))
        passed &= ok("预览返回分块", code == 200 and len(pv["chunks"]) > 0,
                     f"{len(pv['chunks'])} 段")
        passed &= ok("分块带正文", all(c["text"] for c in pv["chunks"]))

    print("3) 外部目录：导入 → 登记 → 重建后仍在")
    root = Path(tempfile.mkdtemp(prefix="ragkb-lib-")) / "外部资料"
    root.mkdir(parents=True)
    (root / "规则.md").write_text("# 报销规则\n\n差旅住宿一线城市 600 元封顶。\n", encoding="utf-8")

    code, res = call("POST", "/api/import_folder", {"path": str(root), "copy": False})
    passed &= ok("导入外部目录", code == 200 and res.get("ok"), f"chunks={res.get('chunks')}")

    code, lib = call("GET", "/api/library")
    ext = [it for it in lib["items"] if it["kind"] == "external"]
    passed &= ok("资料库里出现外部目录", len(ext) == 1 and ext[0]["display"] == "外部资料",
                 ext[0]["name"] if ext else "")
    passed &= ok("外部目录带分块数", ext and ext[0]["chunks"] > 0, str(ext[0]["chunks"]) if ext else "")

    code, _ = call("POST", "/api/reindex")
    code, lib2 = call("GET", "/api/library")
    ext2 = [it for it in lib2["items"] if it["kind"] == "external"]
    passed &= ok("重建索引后外部目录还在（关键）", len(ext2) == 1 and ext2[0]["chunks"] > 0,
                 f"chunks={ext2[0]['chunks'] if ext2 else 0}")

    print("4) 外部目录：取消登记")
    code, res = call("POST", "/api/external_remove", {"path": str(root)})
    passed &= ok("取消登记成功", code == 200 and res.get("ok"), f"现有 {res.get('count')} 块")
    code, lib3 = call("GET", "/api/library")
    passed &= ok("资料库里不再有它",
                 not any(it["kind"] == "external" for it in lib3["items"]))
    passed &= ok("对应分块已清掉", lib3["totals"]["chunks"] < lib["totals"]["chunks"],
                 f"{lib['totals']['chunks']} → {lib3['totals']['chunks']}")

    shutil.rmtree(root.parent, ignore_errors=True)
    print("\n" + ("资料库管理正常 ✅" if passed else "有失败项 ❌"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
