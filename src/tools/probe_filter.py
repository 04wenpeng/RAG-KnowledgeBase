# -*- coding: utf-8 -*-
"""把各类文件丢给入库过滤器，看哪些能进、哪些被挡、理由是什么。"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.loaders import is_ingestible

ROOT = Path(tempfile.mkdtemp(prefix="ragkb-probe-"))


def make(name: str, content: str = "", size_kb: int = 0, binary: bool = False) -> Path:
    p = ROOT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        p.write_bytes(b"\x00" * (size_kb * 1024))
    elif size_kb:
        line = content or "正常的会议纪要内容，每行一句话，没有时间戳。\n"
        p.write_text(line * max(1, size_kb * 1024 // max(1, len(line.encode()))), encoding="utf-8")
    else:
        p.write_text(content or "正常文档内容", encoding="utf-8")
    return p


LOG_LINES = "".join(
    f"T3024 000:{i:03d}.495   SEGGER J-Link Logging line {i}\n" for i in range(200)
)

CASES = [
    # (文件名, 内容/大小, 期望)
    ("产品手册.pdf", "", "应入库"),
    ("会议纪要.md", "# 会议纪要\n\n讨论了三个议题。\n", "应入库"),
    ("常见问题.csv", "问题,答案\n怎么报销,提交单据\n", "应入库"),
    ("接口说明.json", '{"a": 1}', "应入库"),
    ("JLinkLog.txt", "log line\n" * 100, "应挡：文件名像日志"),
    ("build.log", "compile ok\n" * 100, "应挡：后缀黑名单"),
    ("images_md5.json", '{"a":"b"}', "应挡：校验清单"),
    ("数据库.tmp", "tmp", "应挡：后缀黑名单"),
    ("备份.bak", "bak", "应挡：后缀黑名单"),
    ("采集输出.txt", LOG_LINES, "应挡：内容像日志"),
    ("大文档.txt", "", "应挡：纯文本超 1MB（SIZE:1500）"),
    ("超大手册.pdf", "", "应挡：文件超 50MB（SIZE:60000）"),
]


def main() -> int:
    print(f"探测目录：{ROOT}\n")
    print(f"{'文件':<16}{'大小':>10}  {'结果':<4} 说明")
    print("-" * 88)
    for name, content, expect in CASES:
        size_kb = 0
        if "SIZE:" in expect:
            size_kb = int(expect.split("SIZE:")[1].rstrip("）)"))
            expect = expect.split("（")[0]
        binary = name.endswith(".pdf")
        p = make(name, content, size_kb, binary=binary)
        ok, reason = is_ingestible(p)
        kb = p.stat().st_size / 1024
        verdict = "入库" if ok else "跳过"
        print(f"{name:<16}{kb:>8.0f}KB  {verdict:<4} {reason or '（无）'}")
    print("-" * 88)
    print("\n规则是启发式的，两端都有代价：")
    print("  · 误伤：1MB 以上的正常文本文档也会被挡（少数长手册受影响）")
    print("  · 漏网：小体积日志（<100KB）不做内容判定，会照常入库")
    print(f"\n探测文件留在 {ROOT}，可删。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
