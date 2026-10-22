# 源码索引（`src\`）

知识库的全部代码都在这个目录里。**运行时数据不在这里**——`data\`、`store\`、`config\`
在上一级项目根目录。

```
E:\RAG-KnowledgeBase\
├── src\              ← 代码（本目录）
├── data\             ← 你的原始文档
├── store\            ← 向量库（Chroma 持久化）
├── config\           ← API 配置 / 对话历史 / 跳过记录
├── .venv\            ← Python 环境
└── *.bat             ← 启动器
```

---

## 一、入口：三个程序

| 文件 | 行数 | 干什么 | 怎么跑 |
|---|---|---|---|
| `web.py` | 765 | **网页服务**：三个页面 + 全部 HTTP 接口 | `python src\web.py` 或双击 `3-网页版.bat` |
| `ingest.py` | 112 | **建库**：扫描 `data\` → 切块 → 向量化 → 入库；带 `--watch` 自动同步 | `python src\ingest.py --reset` |
| `ask.py` | 102 | **命令行问答**：连续对话 / 单次提问 / 只看检索 | `python src\ask.py "问题"` |

接口清单在 `web.py` 顶部注释里；路由都在 `do_GET` / `do_POST` 两个方法。

---

## 二、`ragkb\`：RAG 流水线（按数据流顺序读）

```
文档 → 加载 → 分割 → 向量化 → 存储 → 检索 → 拼提示词 → 生成 → 答案
      loaders  splitters  embedder  store  retriever  generator
```

| 文件 | 行数 | 职责 | 关键函数 / 类 |
|---|---|---|---|
| `config.py` | 153 | 全局参数、`.env` 读取、嵌入与对话模型的选择 | `BASE_DIR` `CHUNK_SIZE` `embeddings_backend()` `llm_config()` |
| `loaders.py` | 237 | 各种格式 → `Document`；**入库前的过滤规则** | `load_file()` `load_all()` `is_ingestible()` `SKIP_SUFFIXES` |
| `pdf_reader.py` | 340 | 纯标准库 PDF 解析（不依赖 pypdf 的兜底，能修"字间带空格"） | `extract_pdf()` |
| `splitters.py` | 132 | 中文文本分割：分隔符优先级、短块合并、重叠 | `split_text()` `split_documents()` `split_markdown()` |
| `embedder.py` | 84 | 离线哈希向量（无 Key 时的语义替代方案） | `terms()` `vectorize_one()` `HashingEmbedder` |
| `store.py` | 235 | 向量库：Chroma 为主、numpy 兜底；清空/重建/统计 | `VectorStore` `reset_contents()` `built_embedder()` |
| `retriever.py` | 125 | 混合检索：BM25 + 向量余弦，同页去重、代码页/链接页降权 | `Retriever.search()` `_bm25()` |
| `generator.py` | 137 | 提示词模板、调大模型、离线抽取式兜底 | `PROMPT_TEMPLATE` `call_llm()` `extractive_answer()` |
| `rag.py` | 64 | 主流程：检索 → 增强 → 生成 | `RAGKB.ask()` `retrieve()` `reload()` |
| `pipeline.py` | 93 | 建库流水线（命令行与网页共用） | `build_index()` |

## 三、`ragkb\`：状态与配置存储

| 文件 | 行数 | 职责 | 落盘位置 |
|---|---|---|---|
| `profiles.py` | 319 | API 配置的增删改查、启用、连通性测试 | `config\llm_profiles.json` |
| `chats.py` | 114 | 对话保存/读取/重命名/删除 | `config\chats\*.json` |
| `sources.py` | 91 | 外部目录登记（"填路径导入"不复制文件，靠它记住） | `config\external_sources.json` |
| `skips.py` | 67 | 记录被过滤的文件及原因 | `config\ingest.log` |

---

## 四、`ui.py`：三个页面的前端

**1711 行，纯 HTML/CSS/JS 字符串，没有前端构建、没有 npm。**

| 常量 | 页面 |
|---|---|
| `PAGE_ASK` | 知识库问答（对话列表、提问、资料区、拖拽上传） |
| `PAGE_LIBRARY` | 资料库（表格、预览、删除、跳过记录） |
| `PAGE_CONFIG` | API 配置（表格 + 弹窗） |
| `SHARED_CSS` / `TOAST` | 共享样式与通用 JS（`esc` / `api` / `toast`） |
| `CONFIG_SELFTEST` / `UPLOAD_SELFTEST` | 仅 `?selftest=` 时注入的自测脚本 |

改界面后**必须**跑 `src\tools\check_js.py`——页面是 Python 字符串，JS 里写 `'\n'`
会被 Python 解析成真换行，服务端不报错、浏览器白屏。

---

## 五、`agent\`：给其它 Agent 调用

| 文件 | 用途 |
|---|---|
| `rag_client.py` | 纯标准库 HTTP 客户端（可当模块、也可命令行） |
| `langchain_tool.py` | 包成 LangChain 工具（`knowledge_base_ask` / `knowledge_base_search`） |
| `mcp_server.py` | MCP 服务（stdio JSON-RPC），给 Claude Desktop / Cursor / 百炼 |
| `openai_tool.json` | OpenAI function-calling 的 schema |
| `AGENT_INSTRUCTIONS.md` | 告诉别的 Agent 何时/如何用这个库（提示词模板） |

详见 `agent\README.md`。

---

## 六、`tools\`：测试、诊断、演示

| 脚本 | 作用 |
|---|---|
| `test_ui.py` | 布局与元素结构（含三页外壳一致性） |
| `test_ui_flow.py` | 无头浏览器真实点击：切换服务商时名称跟随 |
| `test_web.py` / `test_web2.py` | 接口 CRUD；重建索引与嵌入不一致告警 |
| `test_upload.py` / `test_folder.py` | 单文件上传；整个文件夹导入 |
| `test_filter.py` / `probe_filter.py` | 噪声过滤 + 删除；过滤规则逐项探测 |
| `test_library.py` / `test_chats.py` | 资料库管理；对话保存 |
| `test_agent_api.py` | HTTP 客户端 / LangChain 工具 / MCP 三条链路 |
| `check_js.py` | 三个页面的 JS 语法（node --check） |
| `check_llm.py` | 命令行自检当前启用的模型 |
| `doctor.py` | 打不开时：端口 / HTTP / 代理 / 索引一次查完 |
| `start_daemon.py` / `stop_daemon.py` / `open_page.py` | 后台启动、停止、只开页面 |
| `demo_embedding.py` / `demo_topk.py` | 演示嵌入模型与 Top-K 的效果差异 |
| `debug_search.py` | 打印检索命中的 BM25/向量分量 |

跑测试：

```bat
.venv\Scripts\python.exe src\tools\test_ui.py 8000
.venv\Scripts\python.exe src\tools\check_js.py 8000
.venv\Scripts\python.exe src\tools\test_agent_api.py 8000
```

---

## 七、依赖（`requirements.txt` 在项目根）

```
Python 3.12.14
langchain 1.4.6 · langchain-chroma 1.1.0 · langchain-community 0.4.2
chromadb 1.5.9 · numpy 2.5.4 · pypdf 6.21.1 · openpyxl 3.1.5 · dashscope 1.27.8
```

LangChain 只用在三处：向量库（`langchain_chroma.Chroma`）、嵌入模型
（`DashScopeEmbeddings` / `OllamaEmbeddings`）、Agent 工具（`langchain_core.tools`）。
加载、分割、检索、生成都是自研，原因见项目根 README 的「到底用到了 LangChain 的哪几处」。
