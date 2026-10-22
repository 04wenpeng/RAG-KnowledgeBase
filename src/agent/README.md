# 给其它 Agent 调用知识库

> 要给别的 Agent 写「什么时候该调这个库」的提示词，见 [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md)（中英文模板 + 各宿主放置位置）。

> **鉴权说明（重要）**：知识库只开放"读"的能力给任何人，写操作要管理员口令。
>
> | 能力 | 需要口令 |
> |---|---|
> | 提问 `/api/ask`、检索 `/api/search`、`/api/stats`、`/api/whoami` | 不需要 |
> | 上传资料 `/api/upload`、重建索引、改配置、删资料 | 需要（`admin_password`） |
>
> 所以大多数 agent 只要"读"，什么凭证都不用配。

知识库对外只有一个前提：**服务在跑**（`python web.py` 或双击 `3-网页版.bat`），
默认地址 `http://127.0.0.1:8000`。下面四种接入方式，从最轻到最标准。

---

## 方式一：HTTP 接口（任何语言）

最通用的两种调用：

```bash
# 1) 检索 + 生成（要答案，带出处）
curl -X POST http://127.0.0.1:8000/api/ask ^
     -H "Content-Type: application/json" ^
     -d "{\"question\": \"什么是向量数据库\", \"k\": 4, \"use_llm\": true}"

# 2) 只检索（要原文片段，自己组织答案）
curl -X POST http://127.0.0.1:8000/api/search ^
     -H "Content-Type: application/json" ^
     -d "{\"query\": \"chunk_size\", \"k\": 3}"
```

返回（`/api/ask`）：

```json
{
  "question": "什么是向量数据库",
  "answer": "向量数据库是……[1][2]",
  "mode": "llm",
  "note": "",
  "sources": [
    {"index": 1, "source": "LangChain-RAG-Agent课件.pdf", "page": 4,
     "score": 0.833, "snippet": "型将片段转换为向量…"}
  ]
}
```

返回（`/api/search`）：

```json
{"query": "chunk_size",
 "hits": [{"index": 1, "source": "…", "page": 73, "score": 0.99, "content": "全文片段…"}]}
```

其它可用接口：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/stats` | 索引块数、文件数、当前模型 |
| POST | `/api/ask` | 检索 + 生成 |
| POST | `/api/search` | 只检索 |
| POST | `/api/upload?name=文件名` | 上传文件入库（body 为原始字节） |
| POST | `/api/import_folder` | 导入本机文件夹 `{"path":"D:/资料"}` |
| GET | `/api/library` | 资料库清单（含每文件分块数） |
| DELETE | `/api/files?name=路径` | 删除某个资料 |

---

## 方式二：Python 客户端（推荐给脚本/自定义 agent）

```python
import sys
sys.path.insert(0, r"E:\RAG-KnowledgeBase\src\agent")
from rag_client import RAGClient

kb = RAGClient()                       # 只读：不需要任何口令
print(kb.ask("公司差旅住宿标准是多少？")["answer"])
for hit in kb.search("chunk_size", k=3):
    print(hit["source"], hit["page"], hit["score"])

# 需要往库里加文档时才带口令（会自动登录）
kb_admin = RAGClient(admin_password="123456")
kb_admin.add_document(r"D:\资料\新制度.pdf")
```

局域网里的其它机器直接把地址换成 `http://172.22.124.143:8000` 即可，读操作同样免口令。


```python
import sys
sys.path.insert(0, r"E:\RAG-KnowledgeBase\agent")
from rag_client import RAGClient

kb = RAGClient("http://127.0.0.1:8000")
print(kb.ask("公司差旅住宿标准是多少？")["answer"])
for hit in kb.search("chunk_size", k=3):
    print(hit["source"], hit["page"], hit["score"])
```

命令行也能直接用：

```bash
.venv\Scripts\python.exe agent\rag_client.py "什么是 RAG"
.venv\Scripts\python.exe agent\rag_client.py --search "chunk_size"
.venv\Scripts\python.exe agent\rag_client.py --health
```

---

## 方式三：LangChain / LangGraph 工具（本仓的 venv 已具备依赖）

```python
from agent.langchain_tool import TOOLS
from langgraph.prebuilt import create_react_agent
from langchain_community.llms.tongyi import Tongyi

agent = create_react_agent(Tongyi(model="qwen-plus"), TOOLS)
print(agent.invoke({"messages": [("user", "RAG 的优势和挑战？")]}))
```

两个工具：

| 工具 | 作用 |
|---|---|
| `knowledge_base_ask(question)` | 检索 + 生成，返回带出处的答案 |
| `knowledge_base_search(query, top_k)` | 只检索，返回原文片段 |

自测：

```bash
.venv\Scripts\python.exe agent\langchain_tool.py "什么是向量数据库"
```

---

## 方式四：MCP 服务（Claude Desktop / Cursor / 百炼 等）

`agent/mcp_server.py` 是一个标准 MCP 服务（stdio、JSON-RPC 2.0），暴露三个工具：
`ask_knowledge_base`、`search_knowledge_base`、`knowledge_base_status`。

客户端配置（Claude Desktop 的 `claude_desktop_config.json`，或 Cursor 的 `mcp.json`）：

```json
{
  "mcpServers": {
    "rag-knowledge-base": {
      "command": "E:/RAG-KnowledgeBase/.venv/Scripts/python.exe",
      "args": ["E:/RAG-KnowledgeBase/agent/mcp_server.py"],
      "env": { "RAG_KB_URL": "http://127.0.0.1:8000" }
    }
  }
}
```

命令行自测（一行一个 JSON-RPC 消息）：

```bash
echo {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}} | .venv\Scripts\python.exe agent\mcp_server.py
echo {"jsonrpc":"2.0","id":2,"method":"tools/list"} | .venv\Scripts\python.exe agent\mcp_server.py
echo {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ask_knowledge_base","arguments":{"question":"什么是 RAG"}}} | .venv\Scripts\python.exe agent\mcp_server.py
```

---

## 给 OpenAI 风格 function calling 用的工具定义

`agent/openai_tool.json` 是现成的 schema，直接塞进 `tools` 数组即可；
模型返回 `function_call` 后，把参数转给 `/api/ask`。

---

## 几个实践建议

1. **让 agent 优先用 `search` 还是 `ask`？**
   `ask` 更省事（答案已经组织好，带出处）；需要多步推理、引用精确条款时用 `search`，
   让 agent 自己读原文。
2. **召回数量 k**：默认 4。agent 通常比人更依赖上下文，可以给到 6~8。
3. **并发**：服务是 `ThreadingHTTPServer`，多个 agent 并发调用没问题；但**建库/删除**类操作
   有全局锁，同一时刻只跑一个。
4. **失败要能看见**：`/api/ask` 在知识库为空或没配模型时会返回 `mode: "extractive"` /
   `"no_hit"`，并在 `note` 里说明原因，不要当作正常答案。
5. **别把 Key 交给 agent**：agent 只调本机 HTTP 接口，大模型 Key 只存在服务端
   `config/llm_profiles.json`，不出本机。
