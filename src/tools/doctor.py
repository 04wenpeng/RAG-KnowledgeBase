# -*- coding: utf-8 -*-
"""一键诊断：为什么浏览器打不开？

用法： 双击 7-诊断.bat    或    .venv\\Scripts\\python.exe tools\\doctor.py

它不依赖浏览器，直接在系统层面检查：
  1. 端口有没有在监听（IPv4 / IPv6）
  2. 用 HTTP 真的请求一次（127.0.0.1 / localhost / [::1]）
  3. 系统代理设置会不会劫持 localhost
  4. 索引与配置是否正常
最后给一句明确结论和下一步该干什么。
"""
from __future__ import annotations

import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragkb.config import setup_stdio

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
URLS = [
    f"http://127.0.0.1:{PORT}/",
    f"http://localhost:{PORT}/",
    f"http://[::1]:{PORT}/",
]


def mark(ok: bool) -> str:
    return "✅" if ok else "❌"


def check_listen(addr: str) -> bool:
    family = socket.AF_INET6 if ":" in addr else socket.AF_INET
    s = socket.socket(family, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        return s.connect_ex((addr, PORT)) == 0
    except OSError:
        return False
    finally:
        s.close()


def check_http(url: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ragkb-doctor"})
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read(400).decode("utf-8", "replace")
        return r.status == 200, f"HTTP {r.status}，返回 {len(body)}+ 字节"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def proxy_info() -> dict:
    """读 Windows 系统代理（浏览器默认走这个）。"""
    info = {"enable": 0, "server": "", "override": "", "autoconfig": ""}
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        )
        for name, field in (
            ("ProxyEnable", "enable"),
            ("ProxyServer", "server"),
            ("ProxyOverride", "override"),
            ("AutoConfigURL", "autoconfig"),
        ):
            try:
                info[field] = winreg.QueryValueEx(key, name)[0]
            except OSError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        info["error"] = str(e)
    return info


def main() -> int:
    setup_stdio()
    print("=" * 66)
    print(f"  RAG 知识库 · 打开失败诊断（端口 {PORT}）")
    print("=" * 66)

    print("\n[1] 端口监听")
    v4 = check_listen("127.0.0.1")
    v6 = check_listen("::1")
    print(f"  {mark(v4)} 127.0.0.1:{PORT}")
    print(f"  {mark(v6)} [::1]:{PORT}"
          + ("" if v6 else "   （只监听 IPv4，用 127.0.0.1 访问即可）"))

    print("\n[2] HTTP 实连（绕过浏览器）")
    results = {}
    for url in URLS:
        ok, detail = check_http(url)
        results[url] = ok
        print(f"  {mark(ok)} {url}  {detail}")

    print("\n[3] 系统代理（浏览器会遵守，可能劫持 localhost）")
    p = proxy_info()
    enabled = int(p.get("enable") or 0) == 1
    print(f"  代理开关 : {'开启' if enabled else '关闭'}"
          + (f"  → {p.get('server')}" if p.get("server") else ""))
    if p.get("autoconfig"):
        print(f"  PAC 脚本 : {p.get('autoconfig')}")
    if enabled:
        override = str(p.get("override") or "")
        bypass = any(x in override for x in ("127.0.0.1", "localhost", "<local>"))
        print(f"  绕过列表 : {override or '(空)'}")
        print(f"  {mark(bypass)} localhost/127.0.0.1 在绕过列表里"
              + ("" if bypass else "  ← 这里很可能就是打不开的原因"))

    print("\n[4] 索引与配置")
    try:
        from ragkb.rag import RAGKB

        kb = RAGKB()
        st = kb.store.stats()
        print(f"  {mark(st['exists'])} 索引：{st['count']} 块 / {len(st['files'])} 文件"
              f"（{st['backend']}）")
    except Exception as e:
        print(f"  ❌ 索引读取失败：{type(e).__name__}: {e}")
    try:
        from ragkb import profiles

        prof = profiles.list_profiles()
        active = next((x for x in prof if x.get("active")), None)
        print(f"  {mark(bool(active))} API 配置：{len(prof)} 套"
              + (f"，启用中「{active['name']}」（{active['model']}）" if active else "，尚未配置"))
    except Exception as e:
        print(f"  ❌ 配置读取失败：{type(e).__name__}: {e}")

    print("\n" + "=" * 66)
    print("  结论")
    print("=" * 66)
    if not v4 and not v6:
        print("  服务没在运行。双击 3-网页版.bat（或 4-API配置.bat）启动，")
        print("  窗口别关，它会一直提供页面。")
    elif not results[URLS[0]]:
        print("  端口在监听但 HTTP 请求失败——可能是服务刚崩了，重启一次：")
        print("  关掉所有 python 窗口后重新双击 3-网页版.bat。")
    elif all(results.values()):
        print("  服务完全正常，三地址都能访问。浏览器打不开就是客户端问题，按顺序试：")
        print("   1. 地址栏改成 http://127.0.0.1:8000/  （不要用 https，不要用 localhost）")
        print("   2. 关掉 Clash / VPN 的系统代理，或把 127.0.0.1、localhost 加入绕过列表")
        print("   3. 换一个浏览器（或用无痕窗口）试一次")
        print("   4. 检查是否装了广告拦截/代理类扩展，先禁用")
        if enabled and not any(x in str(p.get("override") or "")
                              for x in ("127.0.0.1", "localhost", "<local>")):
            print("   ⚠ 你的系统代理正开着且没绕过 localhost，这一条最可疑。")
    else:
        print("  部分地址不可用，优先用可用那一条；若只用 localhost 打不开，")
        print("  直接用 http://127.0.0.1:8000/ 即可。")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
