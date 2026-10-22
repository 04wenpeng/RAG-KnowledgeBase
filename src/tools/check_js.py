# -*- coding: utf-8 -*-
"""页面 JS 语法检查：把两个页面的 <script> 抽出来，用 node --check 校验。

为什么需要它：ui.py 里的页面是 Python 字符串，JS 里写 '\\n' 会被 Python 先解析成
真换行，塞进单引号字符串就直接语法错误，而服务端 Python 完全正常——只能靠浏览器
才发现。这个脚本把这类错误挡在提交之前。

用法：
    python tools/check_js.py                 # 检查运行中的服务（默认 8000）
    python tools/check_js.py 8080
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"

NODE_CANDIDATES = [
    Path.home() / ".dsh/dsh-runtimes/dsh-primary-runtime/dependencies/node/bin/node.exe",
    Path(r"C:\Program Files\nodejs\node.exe"),
]


def find_node() -> str | None:
    for p in NODE_CANDIDATES:
        if p.exists():
            return str(p)
    from shutil import which
    return which("node")


def check_page(name: str, url: str, node: str) -> bool:
    html = urllib.request.urlopen(url, timeout=20).read().decode("utf-8")
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not blocks:
        print(f"  ❌ {name}：没有找到 <script>")
        return False

    tmp = Path(tempfile.gettempdir()) / f"ragkb-js-{name}.js"
    tmp.write_text("\n;\n".join(blocks), encoding="utf-8")
    proc = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode == 0:
        print(f"  ✅ {name}：{len(blocks)} 段脚本语法正确")
        return True

    err = (proc.stderr or "").strip().splitlines()
    print(f"  ❌ {name}：语法错误")
    for line in err[:6]:
        print("     " + line)
    # 把出错行前后打印出来，方便定位
    m = re.search(r":(\d+)\n", (proc.stderr or ""))
    if m:
        lineno = int(m.group(1))
        lines = tmp.read_text(encoding="utf-8").splitlines()
        for i in range(max(0, lineno - 3), min(len(lines), lineno + 2)):
            mark = ">>" if i == lineno - 1 else "  "
            print(f"     {mark} {i + 1:4d}| {lines[i][:110]}")
    return False


def main() -> int:
    node = find_node()
    if not node:
        print("跳过：没找到 node，无法做 JS 语法检查")
        return 0
    print(f"用 {node}")
    print("页面脚本语法检查")
    ok = True
    for name, path in (("问答页", "/"), ("资料库", "/library"), ("配置页", "/config")):
        try:
            ok &= check_page(name, BASE + path, node)
        except Exception as exc:
            print(f"  ❌ {name}：请求失败 {exc}")
            ok = False
    print("\n" + ("JS 语法全部通过 ✅" if ok else "有语法错误 ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
