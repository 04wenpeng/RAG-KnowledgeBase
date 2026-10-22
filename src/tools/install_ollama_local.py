# -*- coding: utf-8 -*-
"""一键接上本地 Ollama：找安装包 → 静默安装 → 拉模型 → 建配置 → 启用。

用法：
    .venv\\Scripts\\python.exe src\\tools\\install_ollama_local.py
    .venv\\Scripts\\python.exe src\\tools\\install_ollama_local.py D:\\某个路径\\OllamaSetup.exe --model qwen3:4b

它会自己在这几个地方找 OllamaSetup.exe：
    下载文件夹、桌面、%TEMP%、项目 dev-data\\
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
KB = "http://127.0.0.1:8000"
OLLAMA_API = "http://127.0.0.1:11434"
MODEL = "qwen3:4b"

SEARCH_DIRS = [
    Path(os.environ.get("USERPROFILE", "")) / "Downloads",
    Path(os.environ.get("USERPROFILE", "")) / "Desktop",
    Path(os.environ.get("TEMP", "")),
    PROJECT / "dev-data",
]


def say(msg: str) -> None:
    print(msg, flush=True)


def ollama_exe() -> Path | None:
    for p in [
        PROJECT / "ollama" / "app" / "ollama.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe",
    ]:
        if p.exists():
            return p
    from shutil import which

    w = which("ollama")
    return Path(w) if w else None


def find_installer(hint: str | None) -> Path | None:
    if hint:
        p = Path(hint)
        return p if p.exists() else None
    for d in SEARCH_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.glob("OllamaSetup*.exe"), key=lambda x: x.stat().st_mtime, reverse=True):
            return p
    return None


def http_ok(url: str, timeout: int = 3) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def wait_port(url: str, seconds: int = 90) -> bool:
    for _ in range(seconds):
        if http_ok(url):
            return True
        time.sleep(1)
    return False


def install(exe: Path) -> bool:
    say(f"[安装] {exe}  ({exe.stat().st_size/1024/1024:.0f} MB)")
    for flags in ("/VERYSILENT /NORESTART /SUPPRESSMSGBOXES", "/S"):
        say(f"       尝试静默参数：{flags}")
        try:
            proc = subprocess.run([str(exe)] + flags.split(), timeout=600)
            say(f"       退出码 {proc.returncode}")
            if ollama_exe():
                return True
        except subprocess.TimeoutExpired:
            say("       超时")
    say("[提示] 静默安装没成功，改为启动图形安装程序，请按提示点「Install」")
    subprocess.Popen([str(exe)])
    return False


def start_server(olex: Path) -> None:
    if http_ok(OLLAMA_API + "/api/tags"):
        say("[服务] Ollama 已在运行")
        return
    app = olex.parent / "ollama app.exe"
    say("[服务] 正在启动 Ollama…")
    if app.exists():
        subprocess.Popen([str(app)], close_fds=True)
    else:
        subprocess.Popen([str(olex), "serve"], close_fds=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if wait_port(OLLAMA_API + "/api/tags", 40):
        say("[服务] 已就绪 127.0.0.1:11434")
    else:
        say("[警告] 服务没起来，可能需要手动启动 Ollama")


def pull(olex: Path, model: str) -> bool:
    say(f"[模型] ollama pull {model}（首次下载，看进度见下）")
    rc = subprocess.call([str(olex), "pull", model])
    if rc != 0:
        say(f"[失败] pull 返回 {rc}")
        return False
    out = subprocess.run([str(olex), "list"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    say("[模型] 已安装：")
    for line in out.splitlines():
        say("       " + line)
    return model.split(":")[0] in out


def api(method: str, path: str, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(KB + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode("utf-8")
        return json.loads(body) if body else {}


def setup_profile(model: str) -> None:
    say("[配置] 检查知识库服务…")
    if not http_ok(KB + "/api/stats", 5):
        say("[跳过] 知识库网页服务没在跑，先双击 8-后台启动.bat，再重跑本脚本")
        return

    profiles = api("GET", "/api/profiles").get("profiles", [])
    exist = next((p for p in profiles if p.get("provider") == "ollama"), None)
    if exist:
        say(f"[配置] 已有 Ollama 档案：{exist['name']}，更新模型名")
        api("PUT", f"/api/profiles/{exist['id']}",
            {"name": exist["name"], "provider": "ollama",
             "base_url": "http://localhost:11434/v1", "model": model,
             "api_key": "", "embedding_mode": exist.get("embedding_mode", "offline"),
             "embedding_model": exist.get("embedding_model", ""),
             "embedding_key": ""})
        pid = exist["id"]
    else:
        res = api("POST", "/api/profiles", {
            "name": "本地 Ollama", "provider": "ollama",
            "base_url": "http://localhost:11434/v1", "model": model,
            "api_key": "", "embedding_mode": "offline",
            "embedding_model": "", "embedding_key": "",
        })
        pid = res["profile"]["id"]
        say(f"[配置] 已创建档案 {pid}")

    say("[配置] 测试连通性…")
    try:
        res = api("POST", f"/api/profiles/{pid}/test")
        ok = res.get("ok")
        say(f"       {'✅ 连通' if ok else '❌ 失败'}：{res.get('message') or res.get('detail') or ''}")
    except Exception as exc:
        say(f"       测试报错：{exc}")

    api("POST", f"/api/profiles/{pid}/activate")
    say("[配置] 已启用该档案 ✅")


def main() -> int:
    hint = sys.argv[1] if len(sys.argv) > 1 else None
    model = MODEL
    if "--model" in sys.argv:
        model = sys.argv[sys.argv.index("--model") + 1]

    olex = ollama_exe()
    if olex:
        say(f"[跳过安装] 已装好：{olex}")
    else:
        exe = find_installer(hint)
        if not exe:
            say("❌ 没找到 OllamaSetup.exe。请下载后放到「下载」文件夹，或把路径作为参数传进来。")
            for d in SEARCH_DIRS:
                say(f"   已查找：{d}")
            return 1
        install(exe)
        olex = ollama_exe()
        if not olex:
            say("❌ 安装后仍未找到 ollama.exe，可能需要手动完成安装")
            return 1
        say(f"[安装] 完成：{olex}")

    start_server(olex)
    if not wait_port(OLLAMA_API + "/api/tags", 30):
        say("❌ Ollama 服务未就绪")
        return 1
    if not pull(olex, model):
        say("❌ 模型没拉下来（网络问题？registry.ollama.ai 需可达）")
        return 1
    setup_profile(model)
    say("\n完成。打开 http://127.0.0.1:8000/ 提问，左下角「生成」应显示 " + model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
