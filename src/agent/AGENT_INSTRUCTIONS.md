# 怎么"告诉"别的 Agent 用这个知识库

分两件事：**① 给它能力（能调）** ＋ **② 给它规矩（什么时候调、怎么用结果）**。
缺任何一个都不好用：只给能力它会瞎调，只给规矩它调不到。

---

## 一、直接可粘贴的系统提示词（中文）

> **`{{KB_URL}}` 是什么**：一个占位符，不是真地址。粘之前必须把它替换成这台知识库的
> 真实地址，提示词里出现 3 次，**全部替换**（不要留花括号，也不要加结尾斜杠 `/`）。
>
> | 对方的 Agent 跑在哪 | 替换成 |
> |---|---|
> | 和知识库同一台电脑 | `http://127.0.0.1:8000` |
> | 同一 WiFi / 局域网的另一台电脑 | `http://172.22.124.143:8000` |
> | 装了 Radmin VPN 的异地电脑 | `http://26.94.195.90:8000` |

### 已经填好的版本（局域网用，直接整段复制，不用改）

```
你可以访问一个本地知识库，它存的是用户自己的文档（产品手册、内部制度、课件等）。
回答与这些资料相关的问题前，必须先查知识库，不要凭记忆回答。

接口（都是 HTTP + JSON，不需要认证）：
1) 检索原文：POST http://172.22.124.143:8000/api/search
   请求：{"query": "关键词或短句", "k": 5}
   返回：{"hits": [{"index", "source", "page", "score", "content"}]}
2) 直接问答：POST http://172.22.124.143:8000/api/ask
   请求：{"question": "完整问题", "k": 5, "use_llm": true}
   返回：{"answer", "mode", "sources": [{"source", "page", "score", "snippet"}], "note"}
3) 看库里有什么：GET http://172.22.124.143:8000/api/stats

使用规则：
- 先 /api/search 判断库里有没有相关内容（一般 score > 0.7 算命中）。
- 需要成段答案时用 /api/ask；需要精确引用条款时用 /api/search 自己读原文。
- 引用时标出来源文件名和页码，例如「（《产品手册》第 12 页）」。
- 如果 /api/ask 返回的 mode 是 "no_hit" 或 answer 说"根据现有资料无法回答"，就
  明确告诉用户知识库里没有这项内容，不要改用你的通用知识编造。
- 明确区分「知识库里的内容」和「你自己的知识」，前者要给出处，后者要说明是通识。
```

### 同机使用的版本

把上面那段里所有的 `http://172.22.124.143:8000` 换成 `http://127.0.0.1:8000` 即可。

### 带占位符的原始模板（要自己换地址时用）

把下面这段放进对方 Agent 的 **system prompt / 自定义指令 / 项目规则**里，把 `{{KB_URL}}`
换成你的地址：

```
你可以访问一个本地知识库，它存的是用户自己的文档（产品手册、内部制度、课件等）。
回答与这些资料相关的问题前，必须先查知识库，不要凭记忆回答。

接口（都是 HTTP + JSON，不需要认证）：
1) 检索原文：POST {{KB_URL}}/api/search
   请求：{"query": "关键词或短句", "k": 5}
   返回：{"hits": [{"index", "source", "page", "score", "content"}]}
2) 直接问答：POST {{KB_URL}}/api/ask
   请求：{"question": "完整问题", "k": 5, "use_llm": true}
   返回：{"answer", "mode", "sources": [{"source", "page", "score", "snippet"}], "note"}
3) 看库里有什么：GET {{KB_URL}}/api/stats

使用规则：
- 先 /api/search 判断库里有没有相关内容（一般 score > 0.7 算命中）。
- 需要成段答案时用 /api/ask；需要精确引用条款时用 /api/search 自己读原文。
- 引用时标出来源文件名和页码，例如「（《产品手册》第 12 页）」。
- 如果 /api/ask 返回的 mode 是 "no_hit" 或 answer 说"根据现有资料无法回答"，就
  明确告诉用户知识库里没有这项内容，不要改用你的通用知识编造。
- 明确区分「知识库里的内容」和「你自己的知识」，前者要给出处，后者要说明是通识。
```

## 二、英文版（有些宿主对英文指令更稳）

```
You have access to a private knowledge base of the user's own documents.
Always query it before answering questions that may relate to those documents.

Endpoints (HTTP+JSON, no auth):
- POST {KB_URL}/api/search  body: {"query": "...", "k": 5}
  -> {"hits":[{"index","source","page","score","content"}]}
- POST {KB_URL}/api/ask     body: {"question": "...", "k": 5, "use_llm": true}
  -> {"answer","mode","sources":[{"source","page","score"}]}
- GET  {KB_URL}/api/stats

Rules:
- Search first; treat score > 0.7 as a hit.
- Use /api/ask for prose answers, /api/search when you must quote exact clauses.
- Always cite file name and page number.
- If mode is "no_hit", or the answer says it cannot answer from the material,
  say the knowledge base has no such content. Never fill the gap with your own memory.
```

---

## 三、按宿主怎么放

### 本机已经配好的两个（不用再动手）

| 工具 | 状态 | 位置 |
|---|---|---|
| **Claude Code** | ✅ MCP 已加，`claude mcp list` 显示 Connected | `C:\Users\Rayna\.claude.json`（用户级，所有项目可用） |
| **Codex CLI** | ✅ 已写入配置，重开 Codex 生效 | `C:\Users\Rayna\.codex\config.toml` 的 `[mcp_servers.rag_kb]` |

两个都挂了同一个 MCP 服务，工具名：`ask_knowledge_base` / `search_knowledge_base` /
`knowledge_base_status`。用的时候直接说「用知识库查一下 XXX」。

### 还没配的：Trae CN

Trae 的 MCP 配置存在它自己的数据库里，不能直接改文件，走界面：

1. Trae 右上角 **设置（齿轮）→ MCP → 添加 / Add MCP Server**
2. 选 **手动配置 / JSON**，粘贴 `agent/mcp_snippet.json` 的内容
3. 保存后应显示绿色「已连接」，工具列表出现 3 个 `*_knowledge_base`

不想配 MCP 也能用：Trae 里能开终端，直接跑
`.venv\Scripts\python.exe src\agent\rag_client.py "问题"`；
或者把 `AGENTS.md` 放到你的项目根目录，让它知道有这么个库。



| 宿主 | 怎么给能力 | 怎么给规矩 |
|---|---|---|
| **Claude Desktop** | 配 MCP（见 `agent/README.md`），工具名 `ask_knowledge_base` / `search_knowledge_base` | 放进 Project 的 custom instructions |
| **Cursor** | 同上配 MCP；或让它在终端跑 `curl` | 写进 `.cursor/rules/kb.mdc`（`alwaysApply: true`） |
| **Claude Code / Codex CLI** | 直接给 shell 权限，让它跑 `python src/agent/rag_client.py "问题"` | 写进 `CLAUDE.md` / `AGENTS.md` |
| **LangChain / LangGraph** | `from agent.langchain_tool import TOOLS` | 放进 `SystemMessage` |
| **Dify / 阿里云百炼应用** | 用「HTTP 请求」节点或自定义工具指向 `/api/ask` | 应用提示词里写上面的规则 |
| **ChatGPT 网页版 / 手机 App** | ⚠️ 调不到你的 localhost，除非有公网地址 | 同上，但需要公网可达（内网穿透或部署到服务器） |

### Claude Code / Cursor 的「零配置」做法

它们能跑命令，所以连 MCP 都不用配，在项目里放个 `AGENTS.md`：

```markdown
## 本地知识库

涉及产品/制度/课件的问题，先跑：

    .venv\Scripts\python.exe src/agent/rag_client.py "你的问题"

命令输出带「出处：文件名 第N页」，引用时保留页码。
如果输出「根据现有资料无法回答」，说明库里没有，不要编。
```

---

## 四、给 function calling 用的工具描述

如果要注册成工具（OpenAI / 百炼 / Dify 都吃这套），用 `agent/openai_tool.json`，
描述里这两句最关键：

```
description: "在本地 RAG 知识库中检索并回答。适用于用户自己的文档类问题；
知识库里没有时会明确说无法回答，不会编造。"
```

工具描述写得越像"什么时候该用"，模型调用得越准。别写成 `"query the kb"`。

---

## 五、接好之后怎么验证

连上后问这三句，行为对了才算接好：

| 问题 | 期望 |
|---|---|
| 「RAG 的优势是什么」 | 给出带页码的答案（课件第 5 页有） |
| 「RAG 的两个阶段分别是什么」 | 说出索引阶段与查询阶段，并给页码 |
| 「今天天气怎么样」 | 明确说"知识库里没有"，**而不是硬编一个天气** |

第三题最能暴露问题：说明它正确区分了"库里有"和"库外"。

---

## 六、三个常见坑

1. **只说"你有知识库"不给接口** → 模型会假装查过。必须给 URL 或工具。
2. **不给"没命中怎么办"的规则** → 模型会拿通用知识填空，答案看起来对、其实是编的。
3. **把管理口令也给出去** → 它就能删你的资料。读接口本来就不需要口令，
   `123456` 别写进任何 agent 的 prompt。
