# -*- coding: utf-8 -*-
"""测试"直接导入一个文件夹"（不复制，读原位置）。用法：python tools/test_folder.py 8000"""
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


def call(method, path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"} if data else {}, method=method)
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
    root = Path(tempfile.mkdtemp(prefix="ragkb-folder-")) / "差旅制度资料"
    (root / "子目录").mkdir(parents=True, exist_ok=True)
    (root / "住宿.md").write_text("# 住宿标准\n\n一线城市每晚不超过 600 元，二线不超过 450 元。\n", encoding="utf-8")
    (root / "子目录" / "交通.txt").write_text("市内交通凭票报销，单日上限 80 元。\n", encoding="utf-8")
    (root / "无用文件.exe").write_bytes(b"MZ")          # 应被忽略

    code, before = call("GET", "/api/stats")
    print(f"导入前：{before['count']} 块 / {len(before['files'])} 文件")

    code, res = call("POST", "/api/import_folder", {"path": str(root), "copy": False})
    passed &= ok("POST /api/import_folder 成功", code == 200 and res.get("ok"),
                 f"files={res.get('file_count')} chunks={res.get('chunks')}")
    passed &= ok("只统计支持的文件（.exe 被忽略）", res.get("file_count") == 2)
    passed &= ok("来源里带上了文件夹名和子目录", any("子目录" in s for s in res.get("sample", [])),
                 "、".join(res.get("sample", [])))

    code, after = call("GET", "/api/stats")
    print(f"导入后：{after['count']} 块 / {len(after['files'])} 文件")
    passed &= ok("索引块数增加", after["count"] > before["count"])
    passed &= ok("来源里出现子目录路径",
                 any("差旅制度资料" in f for f in after["files"]),
                 "、".join(f for f in after["files"] if "差旅" in f))

    code, ans = call("POST", "/api/ask", {"question": "一线城市住宿标准是多少", "k": 4, "use_llm": False})
    hit = any("住宿.md" in (s.get("source") or "") for s in ans.get("sources") or [])
    passed &= ok("导入的文件夹内容可立刻检索", hit,
                 "、".join(s.get("source", "") for s in (ans.get("sources") or [])[:3]))

    code, res = call("POST", "/api/import_folder", {"path": str(root / "不存在")})
    passed &= ok("路径不存在时给出明确错误", code == 400, str(res.get("error"))[:40])

    shutil.rmtree(root.parent, ignore_errors=True)
    print("\n" + ("文件夹导入正常 ✅" if passed else "有失败项 ❌"))
    print("提示：这次导入的块还在索引里，如需清理请把 data 恢复后点「重建索引」")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
