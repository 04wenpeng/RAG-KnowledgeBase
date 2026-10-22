# -*- coding: utf-8 -*-
"""备份知识库：把 data / config（可选 store）打成 zip，自动保留最近 N 份。

公司内部用最怕的不是用不了，是数据丢了。这个脚本适合挂成每天定时任务。

用法：
    .venv\\Scripts\\python.exe src\\tools\\backup.py              # 备份 data + config（几 MB）
    .venv\\Scripts\\python.exe src\\tools\\backup.py --with-index # 连向量库一起备份（约 250 MB）
    .venv\\Scripts\\python.exe src\\tools\\backup.py --keep 5     # 只保留最近 5 份
    .venv\\Scripts\\python.exe src\\tools\\backup.py --list       # 看看有哪些备份
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = ROOT / "backups"
DEFAULT_KEEP = 10


def human(n: int) -> str:
    return f"{n/1024/1024:.1f} MB" if n > 1024 * 1024 else f"{n/1024:.0f} KB"


def do_backup(with_index: bool, keep: int) -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    tag = "full" if with_index else "data"
    out = BACKUP_DIR / f"ragkb-{stamp}-{tag}.zip"

    sources = [ROOT / "data", ROOT / "config"]
    if with_index:
        sources.append(ROOT / "store")

    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for src in sources:
            if not src.exists():
                continue
            for p in sorted(src.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(ROOT))
                    count += 1

    size = out.stat().st_size
    print(f"[备份] {out.name}  {count} 个文件  {human(size)}")

    olds = sorted(BACKUP_DIR.glob("ragkb-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in olds[keep:]:
        old.unlink()
        print(f"[清理] 删除过期备份 {old.name}")

    (BACKUP_DIR / "backup.log").open("a", encoding="utf-8").write(
        f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{out.name}\t{count} files\t{human(size)}\n")
    return 0


def do_list() -> int:
    if not BACKUP_DIR.exists():
        print("还没有任何备份。")
        return 0
    files = sorted(BACKUP_DIR.glob("ragkb-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("还没有任何备份。")
        return 0
    print(f"共 {len(files)} 份备份（{BACKUP_DIR}）：")
    for f in files:
        ts = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {ts}  {f.name:<32} {human(f.stat().st_size)}")
    print("\n恢复方法：解压覆盖到项目根目录（先停服务），再点「重建索引」。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-index", action="store_true", help="连 store/ 向量库一起备份")
    ap.add_argument("--keep", type=int, default=DEFAULT_KEEP, help=f"保留份数，默认 {DEFAULT_KEEP}")
    ap.add_argument("--list", action="store_true", help="列出已有备份")
    args = ap.parse_args()

    if args.list:
        return do_list()

    free = shutil.disk_usage(ROOT).free
    if free < 500 * 1024 * 1024:
        print(f"[警告] 磁盘只剩 {free/1024/1024:.0f} MB，备份可能失败")
    return do_backup(args.with_index, max(1, args.keep))


if __name__ == "__main__":
    sys.exit(main())
