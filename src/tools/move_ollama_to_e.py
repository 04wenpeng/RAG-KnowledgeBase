# -*- coding: utf-8 -*-
"""把 Ollama 的程序和模型全部搬到 E:\\RAG-KnowledgeBase\\ollama\\。

做四件事：
  1. 停掉 Ollama 进程
  2. 搬模型仓库 ~\\.ollama\\models  →  ollama\\models，并设置 OLLAMA_MODELS
  3. 搬程序目录 %LOCALAPPDATA%\\Programs\\Ollama  →  ollama\\app
  4. 修 PATH、开机启动快捷方式、卸载注册表里的路径

用法： .venv\\Scripts\\python.exe src\\tools\\move_ollama_to_e.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

E_ROOT = Path(r"E:\RAG-KnowledgeBase\ollama")
APP_NEW = E_ROOT / "app"
MODELS_NEW = E_ROOT / "models"
APP_OLD = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama"
MODELS_OLD = Path(os.environ["USERPROFILE"]) / ".ollama" / "models"
STARTUP = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

UNINSTALL_KEY = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{44E83376-CE68-45EB-8FC1-393500EB558C}_is1"


def say(msg: str) -> None:
    print(msg, flush=True)


def stop_ollama() -> None:
    say("[1/6] 停止 Ollama 进程")
    for name in ("ollama app.exe", "ollama.exe"):
        subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue "
         "| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
        capture_output=True)
    say("      已停止")


def move_dir(src: Path, dst: Path, label: str) -> None:
    if not src.exists():
        say(f"[跳过] {label}：{src} 不存在")
        return
    if dst.exists():
        say(f"[跳过] {label}：目标已存在 {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    say(f"[搬移] {label}: {src}  →  {dst}")
    shutil.move(str(src), str(dst))
    say("      完成")


def set_user_env(name: str, value: str) -> None:
    subprocess.run(["setx", name, value], capture_output=True)
    os.environ[name] = value
    say(f"[环境] {name} = {value}")


def fix_path() -> None:
    say("[4/6] 修正用户 PATH")
    cur = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "[Environment]::GetEnvironmentVariable('PATH','User')"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    parts = [p for p in cur.split(";") if p and "Programs\\Ollama" not in p and str(APP_NEW) not in p]
    parts.append(str(APP_NEW))
    new = ";".join(parts)
    subprocess.run(["setx", "PATH", new], capture_output=True)
    os.environ["PATH"] = os.environ.get("PATH", "") + ";" + str(APP_NEW)
    say(f"      已把 {APP_NEW} 加进 PATH（旧的已移除）")


def fix_startup() -> None:
    say("[5/6] 重建开机启动快捷方式")
    lnk = STARTUP / "Ollama.lnk"
    exe = APP_NEW / "ollama app.exe"
    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{lnk}'); "
        f"$s.TargetPath = '{exe}'; "
        f"$s.WorkingDirectory = '{APP_NEW}'; "
        "$s.Save()"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode == 0:
        say(f"      {lnk}  →  {exe}")
    else:
        say(f"      失败：{r.stderr.strip()[:120]}")


def fix_uninstall_registry() -> None:
    say("[6/6] 更新卸载注册表里的路径")
    ps = (
        f"$k = '{UNINSTALL_KEY}'; "
        "if (Test-Path $k) { "
        f"Set-ItemProperty $k -Name InstallLocation -Value '{APP_NEW}\\'; "
        f"Set-ItemProperty $k -Name DisplayIcon -Value '{APP_NEW}\\unins000.exe'; "
        "'ok' } else { 'missing' }"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    say(f"      {r.stdout.strip()}")


def main() -> int:
    say(f"目标目录：{E_ROOT}")
    stop_ollama()

    say("[2/6] 搬模型仓库（1.1 GB）")
    move_dir(MODELS_OLD, MODELS_NEW, "模型")
    set_user_env("OLLAMA_MODELS", str(MODELS_NEW))

    say("[3/6] 搬程序目录（2.9 GB）")
    move_dir(APP_OLD, APP_NEW, "程序")

    fix_path()
    fix_startup()
    fix_uninstall_registry()

    say("\n验证：")
    exe = APP_NEW / "ollama.exe"
    if exe.exists():
        out = subprocess.run([str(exe), "list"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        say("  ollama list:")
        for line in out.stdout.splitlines():
            say("    " + line)
    else:
        say(f"  ❌ 找不到 {exe}")
        return 1
    say(f"  C 盘释放：约 4.0 GB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
