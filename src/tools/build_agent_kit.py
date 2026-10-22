# -*- coding: utf-8 -*-
"""打包一个「别的电脑」用的最小 Agent 套件到 dist\\rag-agent-kit\\。

只放运行时必需的东西，全部纯标准库，对方机器只要有 Python 3.10+ 就能跑，
不需要安装 langchain / chromadb，也不需要拷贝 200 多 MB 的向量库。
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(r"E:\RAG-KnowledgeBase")
AGENT = ROOT / "src" / "agent"
OUT = ROOT / "dist" / "rag-agent-kit"

# 换成知识库那台机器的地址（对方电脑要能访问到）
# 用主机名而不是 IP：IP 会随路由器变，主机名稳定
DEFAULT_URL = "http://DESKTOP-M0B255V:8000"


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # 1) 核心：纯标准库的客户端 + MCP 服务
    for name in ("rag_client.py", "mcp_server.py"):
        shutil.copy2(AGENT / name, OUT / name)
        print(f"[复制] {name}")

    # 2) 连通性自检脚本
    (OUT / "check.py").write_text(
        '''# -*- coding: utf-8 -*-
"""检查能不能连上知识库。用法：python check.py [地址]"""
import json, sys, urllib.request, os

url = (sys.argv[1] if len(sys.argv) > 1 else
       os.environ.get("RAG_KB_URL", "%s")).rstrip("/")
print(f"检查 {url} ...")
try:
    with urllib.request.urlopen(url + "/api/stats", timeout=8) as r:
        d = json.loads(r.read().decode())
    print(f"  ✅ 连接成功：索引 {d['count']} 块 / {len(d['files'])} 文件，模型 {d.get('llm') or '离线抽取'}")
    with urllib.request.urlopen(urllib.request.Request(
            url + "/api/ask",
            data=json.dumps({"question": "chunk_size 默认值", "k": 2}).encode(),
            headers={"Content-Type": "application/json"}, method="POST"), timeout=120) as r:
        a = json.loads(r.read().decode())
    print(f"  ✅ 问答正常：{a.get('answer', '')[:60]}")
except Exception as exc:
    print(f"  ❌ 连不上：{type(exc).__name__}: {exc}")
    print("     1) 知识库那台机器是否开着？服务是否在跑？")
    print("     2) 两台机器是否在同一 WiFi / Radmin VPN？")
    print("     3) 地址里的 IP 是否变了？在知识库那台机器上 ipconfig 看一下")
    sys.exit(1)
''' % DEFAULT_URL,
        encoding="utf-8")
    print("[生成] check.py")

    # 3) 命令行提问入口
    (OUT / "ask.bat").write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "cd /d \"%~dp0\"\r\n"
        f"set RAG_KB_URL={DEFAULT_URL}\r\n"
        "set PYTHONIOENCODING=utf-8\r\n"
        "if \"%~1\"==\"\" (\r\n"
        "  echo 用法：ask.bat \"你的问题\"\r\n"
        "  pause\r\n"
        "  exit /b\r\n"
        ")\r\n"
        "python rag_client.py %*\r\n"
        "echo.\r\npause\r\n",
        encoding="utf-8")
    print("[生成] ask.bat")

    (OUT / "check.bat").write_text(
        "@echo off\r\nchcp 65001 >nul\r\ncd /d \"%~dp0\"\r\n"
        f"set RAG_KB_URL={DEFAULT_URL}\r\n"
        "python check.py\r\necho.\r\npause\r\n",
        encoding="utf-8")
    print("[生成] check.bat")

    # 4) 各宿主配置：示例 + 生成器（路径必须按解压位置算，不能写死我这里的目录）
    (OUT / "mcp_claude.example.json").write_text(
        json.dumps({
            "mcpServers": {
                "rag-kb": {
                    "command": "python",
                    "args": ["<解压目录>/mcp_server.py"],
                    "env": {"RAG_KB_URL": DEFAULT_URL},
                }
            }
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    (OUT / "gen_config.py").write_text(f'''# -*- coding: utf-8 -*-
"""按本机解压位置生成 MCP 配置（把 <解压目录> 换成真实路径）。

用法：双击 gen_config.bat，或  python gen_config.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
URL = "{DEFAULT_URL}"
server = str(BASE / "mcp_server.py").replace("\\\\", "/")

claude = {{"mcpServers": {{"rag-kb": {{
    "command": "python",
    "args": [server],
    "env": {{"RAG_KB_URL": URL}},
}}}}}}
(BASE / "mcp_claude.json").write_text(
    json.dumps(claude, ensure_ascii=False, indent=2), encoding="utf-8")

toml = ("[mcp_servers.rag_kb]\\n"
        'command = "python"\\n'
        'args = ["' + server + '"]\\n'
        'env = {{ RAG_KB_URL = "' + URL + '" }}\\n')
(BASE / "mcp_codex.toml").write_text(toml, encoding="utf-8")

print("已生成 mcp_claude.json / mcp_codex.toml")
print("Claude Code 一条命令：")
print("  claude mcp add rag-kb --scope user --env RAG_KB_URL=" + URL + " -- python \\"" + server + "\\"")
''', encoding="utf-8")

    (OUT / "gen_config.bat").write_text(
        "@echo off\r\nchcp 65001 >nul\r\ncd /d \"%~dp0\"\r\n"
        "set PYTHONIOENCODING=utf-8\r\npython gen_config.py\r\necho.\r\npause\r\n",
        encoding="utf-8")
    print("[生成] mcp_claude.example.json / gen_config.py / gen_config.bat")

    # 5) 说明
    (OUT / "README.md").write_text(f"""# 在别的电脑上使用这个知识库

**前提**：知识库那台机器开着，服务在跑；两台机器在同一 WiFi 或同一个 Radmin VPN。

当前内置地址：`{DEFAULT_URL}`
（如果你的 IP 变了，改 `ask.bat` / `check.bat` 里的 `RAG_KB_URL`，或设成系统环境变量）

---

## 一、只用浏览器（什么都不用装）

在浏览器打开：

```
{DEFAULT_URL}/
```

能提问、看历史、浏览资料。改配置需要管理员口令（找知识库主人要）。

## 二、命令行问一嘴

需要 Python 3.10+（安装时勾选 Add to PATH）。

双击 `check.bat` 先自检，看到绿色的「连接成功」就说明通了。

然后：

```bat
ask.bat "chunk_size 默认值多少"
ask.bat --search "chunk_size" -k 3
```

## 三、让本机的 AI Agent 用上

### Claude Code

把 `mcp_claude.json` 里 `rag-kb` 那一段合并进 `~/.claude.json` 的 `mcpServers`，
或者直接：

```bat
claude mcp add rag-kb --scope user -- python "{OUT / 'mcp_server.py'}"
```

（记得先设 `RAG_KB_URL` 环境变量）

### Codex CLI

把 `mcp_codex.toml` 的内容追加到 `%USERPROFILE%\\.codex\\config.toml`。

### Claude Desktop / Trae / Cursor

设置 → MCP → 添加，粘贴 `mcp_claude.json` 的内容。

配好后对 Agent 说：「用知识库查一下 XXX」，它会调 `ask_knowledge_base`。

---

## 为什么这套东西这么小

客户端和 MCP 服务都是**纯标准库**，只有十几 KB。
文档、向量库、模型都在知识库那台机器上，这里只是"遥控器"。

## 连不上时

1. 在知识库那台机器上：`python src\\tools\\service_task.py status`
2. 看它的 IP：`ipconfig`，找 IPv4 地址
3. 防火墙：那台机器若开了防火墙，需要放行 8000 端口
""",
        encoding="utf-8")
    print("[生成] README.md")

    # 6) 打包成 zip，方便直接发过去
    zip_path = ROOT / "dist" / "rag-agent-kit.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(OUT))
    print(f"\n[打包] {zip_path}  ({zip_path.stat().st_size/1024:.0f} KB)")
    print(f"[目录] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
