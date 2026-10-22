# AGENTS.md —— 给在这个目录里工作的 AI Agent 看

> 任何能读文件、能跑命令的 Agent（Codex CLI / Claude Code / Trae / Cursor …）
> 进到这个仓库都应该先读这一页。**如果只是要查知识库内容，不需要读源码。**

## 这里是什么

一个本地 RAG 知识库：文档在 `data\`，向量在 `store\`，服务在 `http://127.0.0.1:8000`。

## 要查知识库内容，用这两条命令

```powershell
# 1) 问问题（返回答案 + 出处，需要服务在跑）
.venv\Scripts\python.exe src\agent\rag_client.py "你的问题"

# 2) 只要原文片段（自己核对、引用时用）
.venv\Scripts\python.exe src\agent\rag_client.py --search "关键词" -k 3
```

也可以走 HTTP（不需要认证）：

```
POST http://127.0.0.1:8000/api/ask     {"question": "...", "k": 4}
POST http://127.0.0.1:8000/api/search  {"query": "...", "k": 4}
GET  http://127.0.0.1:8000/api/stats
```

## 规则

- 回答知识库相关问题时**必须**先查，不要凭记忆答。
- 引用时保留「文件名 + 页码」。
- 命令输出「根据现有资料无法回答」或 `mode=no_hit` → 说明库里没有，**不要编**。
- 不要尝试修改 `data\` / `store\` / `config\`；需要加资料请让用户操作，
  或明确告知需要管理员口令（`config\access.json`）。
- 改代码后必须跑 `src\tools\check_js.py`（改 UI 时）与相关 `src\tools\test_*.py`。

## 服务没起的时候

```powershell
.venv\Scripts\python.exe src\tools\service_task.py start     # 启动（计划任务托管）
.venv\Scripts\python.exe src\tools\service_task.py status    # 看状态
```
