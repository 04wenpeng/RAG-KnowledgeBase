# -*- coding: utf-8 -*-
"""测试网页上传入库：上传一个 txt，看索引是否真的变大。用法：python tools/test_upload.py 8000"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"

SAMPLE = """示例资料：差旅报销标准

一、住宿标准
一线城市每晚不超过 600 元，二线城市不超过 450 元，其他城市不超过 350 元。
超标部分由个人承担 50%。

二、交通标准
市内交通凭票报销，单日上限 80 元。高铁二等座可报销，一等座需事先审批。

三、报销时限
出差结束后 15 个自然日内提交报销单，逾期需要部门负责人签字说明。
"""


def call(method, path, data=None, raw=None, headers=None):
    body = raw if raw is not None else (json.dumps(data, ensure_ascii=False).encode() if data else None)
    h = headers or ({"Content-Type": "application/json"} if data else {})
    req = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))


def ok(label, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + label + (f"  {extra}" if extra else ""))
    return bool(cond)


def main() -> int:
    passed = True

    code, before = call("GET", "/api/stats")
    print(f"上传前：{before['count']} 块 / {len(before['files'])} 文件")

    name = "差旅报销标准（上传测试）.txt"
    code, res = call("POST", "/api/upload?name=" + urllib.request.quote(name),
                     raw=SAMPLE.encode("utf-8"),
                     headers={"Content-Type": "text/plain"})
    passed &= ok("POST /api/upload 成功", code == 200 and res.get("ok"), f"chunks={res.get('chunks')}")

    code, after = call("GET", "/api/stats")
    print(f"上传后：{after['count']} 块 / {len(after['files'])} 文件")
    passed &= ok("索引块数增加", after["count"] > before["count"],
                 f"+{after['count'] - before['count']} 块")
    passed &= ok("文件数增加", len(after["files"]) > len(before["files"]))
    passed &= ok("文件名出现在来源里", name in after["files"])

    code, files = call("GET", "/api/files")
    passed &= ok("GET /api/files 能列出它", any(f["name"] == name for f in files["files"]))

    # 立刻就能问出来（验证检索已重建）
    code, ans = call("POST", "/api/ask", {"question": "一线城市住宿标准是多少", "k": 4, "use_llm": False})
    hit = any(name in (s.get("source") or "") for s in ans.get("sources") or [])
    passed &= ok("刚上传的资料立刻能被检索到", hit,
                 "、".join(s.get("source", "") for s in (ans.get("sources") or [])))
    if hit:
        top = next(s for s in ans["sources"] if name in (s.get("source") or ""))
        print("     命中片段：", top["snippet"][:60].replace("\n", " "))

    # 不支持的格式应被拒绝
    code, res = call("POST", "/api/upload?name=bad.exe", raw=b"MZ", headers={"Content-Type": "application/octet-stream"})
    passed &= ok("拒绝不支持的格式", code == 400, f"HTTP {code}")

    print("\n" + ("上传链路正常 ✅" if passed else "有失败项 ❌"))
    print(f"注意：测试文件已写入 data/，如需清理请删除「{name}」后运行 ingest.py --reset")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
