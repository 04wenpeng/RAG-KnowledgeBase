# -*- coding: utf-8 -*-
"""把项目自己的说明文档同步进 data/（让知识库能回答"这个库怎么用"）。

注意：**重建索引时会自动调用**，一般不需要单独跑这个脚本。
只有在不重建索引、只想先看看有没有差异时才需要。

用法：
    .venv\\Scripts\\python.exe src\\tools\\sync_docs_to_data.py
    .venv\\Scripts\\python.exe src\\tools\\sync_docs_to_data.py --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ragkb.docsync import SOURCES, check, sync  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告差异，不写文件")
    args = ap.parse_args()

    if args.check:
        rows = check()
        drift = 0
        for name, dirty in rows:
            print(f"  {'[需更新]' if dirty else '[一致]  '} {name}")
            drift += int(dirty)
        print(f"\n共 {len(rows)} 个文档，{drift} 个需要同步。" if drift else "\n全部一致。")
        return 0

    changed = sync(verbose=True)
    if changed:
        print(f"\n已同步 {len(changed)} 个文档。重建索引后生效：")
        print("  网页：资料库页点「重建索引」")
        print("  或：  .venv\\Scripts\\python.exe src\\ingest.py")
    else:
        print("全部一致，无需操作。")
    print(f"\n同步清单（{len(SOURCES)} 个）：")
    for rel, name in SOURCES:
        print(f"  {rel}  ->  data/项目说明/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
