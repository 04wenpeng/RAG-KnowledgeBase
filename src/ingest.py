# -*- coding: utf-8 -*-
"""建库脚本：data/ -> 切块 -> 向量化 -> 存入向量库。

用法：
    python ingest.py                     # 增量追加（相同 id 覆盖）
    python ingest.py --reset             # 清空后重建
    python ingest.py --chunk-size 800 --overlap 80
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ragkb.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION,
    DATA_DIR,
    embedding_hint,
    ensure_dirs,
    setup_stdio,
)
from ragkb.loaders import SUPPORTED
from ragkb.pipeline import build_index


def _scan(data_dir: Path) -> dict:
    """目录里所有可解析文件的 修改时间。"""
    out = {}
    for p in data_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith(("~$", ".")):
            try:
                out[p] = p.stat().st_mtime
            except OSError:
                pass
    return out


def watch(data_dir: Path, chunk_size: int, chunk_overlap: int) -> int:
    """盯着 data 目录，文件一改就单独入库，不用手动跑脚本。"""
    print("=" * 68)
    print("  资料自动同步已开启")
    print(f"  监听目录 : {data_dir}")
    print("  用法     : 把文件复制/拖进这个目录，2 秒内自动切块入库")
    print("  停止     : Ctrl+C")
    print("=" * 68)
    known = _scan(data_dir)
    print(f"  当前 {len(known)} 个文件已在监视中\n")
    try:
        while True:
            time.sleep(2)
            cur = _scan(data_dir)
            changed = [p for p, m in cur.items() if known.get(p) != m]
            removed = [p for p in known if p not in cur]
            for p in changed:
                print(f"[{time.strftime('%H:%M:%S')}] 检测到 {p.name}，正在入库 …")
                result = build_index(files=[p], chunk_size=chunk_size,
                                     chunk_overlap=chunk_overlap, verbose=False)
                if result.get("ok"):
                    print(f"             ✓ 切分 {result['chunks']} 块，索引现有 "
                          f"{result['stats']['count']} 块 / {len(result['stats']['files'])} 文件")
                else:
                    print(f"             ✗ {result.get('error')}")
            for p in removed:
                print(f"[{time.strftime('%H:%M:%S')}] {p.name} 已从目录删除"
                      f"（旧索引还在，需要 --reset 才会清掉）")
            known = cur
    except KeyboardInterrupt:
        print("\n已停止监听。")
    return 0


def main() -> int:
    setup_stdio()
    parser = argparse.ArgumentParser(description="构建 RAG 知识库索引")
    parser.add_argument("--data", default=str(DATA_DIR), help="文档目录（默认 data/）")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    parser.add_argument("--reset", action="store_true", help="清空已有索引后重建")
    parser.add_argument("--watch", action="store_true",
                        help="开启监听：data 目录里一有文件变化就自动入库")
    args = parser.parse_args()

    ensure_dirs()
    data_dir = Path(args.data)
    if not data_dir.exists():
        print(f"[错误] 文档目录不存在：{data_dir}")
        return 1

    if args.watch:
        return watch(data_dir, args.chunk_size, args.overlap)

    print("=" * 68)
    print("  RAG 知识库 · 建库")
    print("=" * 68)
    print(f"  文档目录 : {data_dir}")
    print(f"  分块参数 : chunk_size={args.chunk_size}  overlap={args.overlap}")
    print(f"  嵌入模型 : {embedding_hint()}")
    print(f"  collection: {COLLECTION}")
    print("-" * 68)

    t0 = time.time()
    print("[1/3] 加载文档 + 文本分割 ...")
    result = build_index(
        data_dir=data_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        reset=args.reset,
        verbose=True,
    )
    if not result.get("ok"):
        print(f"\n[提示] {result.get('error')}")
        return 1

    print(f"[2/3] 切分为 {result['chunks']} 个文本块")
    print(f"[3/3] 向量化写入 {result['backend']}（{'已清空旧索引' if args.reset else '相同 id 覆盖'}）")

    print("-" * 68)
    print(f"  完成：写入 {result['chunks']} 个块，耗时 {time.time() - t0:.1f}s")
    print(f"  向量库后端 : {result['backend']}")
    print(f"  索引总量   : {result['stats']['count']} 块 / {result['total_chars']:,} 字")
    print(f"  来源文件   : {', '.join(result['stats']['files'][:8])}"
          f"{' ...' if len(result['stats']['files']) > 8 else ''}")
    print("=" * 68)
    print("  下一步： python ask.py   或   python web.py（网页里可配 API）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
