# RAG 知识库（LangChain 版）

一个可以在本机直接跑起来的企业知识库问答系统：把 `data/` 里的文档灌进去，
用自然语言提问，答案带出处（第几页、哪一行）。

对应教程：`2027版本 基于LangChain的RAG与Agent智能体开发视频教程`

---

## 一、30 秒上手

1. 双击 **`1-建库.bat`** —— 把 `data/` 里的文档切块、向量化、写进索引
2. 双击 **`2-提问.bat`** —— 命令行问答
3. 或者双击 **`3-网页版.bat`** —— 浏览器打开 `http://127.0.0.1:8000`

首次使用前已经装好依赖（`.venv` 目录），不用再装。

---

## 二、目录结构

```
E:\RAG-KnowledgeBase\
├── 0-打开网页.bat … 9-停止服务.bat      ← 启动器（共 10 个，见下表）
├── README.md                           本文件
├── requirements.txt                    依赖清单
├── .env / .env.example                 环境变量（模型 Key 也可写这里）
│
├── src\                                ← 全部代码（详细索引见 src\README.md）
│   ├── web.py                          网页服务：路由 + 全部 HTTP 接口
│   ├── ui.py                           三个页面的 HTML/CSS/JS 模板
│   ├── ingest.py                       命令行建库（--reset / --watch）
│   ├── ask.py                          命令行问答
│   ├── ragkb\                          RAG 流水线
│   │   ├── config.py                   全局参数 / .env / 模型选择
│   │   ├── loaders.py                  文档加载 + 入库过滤规则
│   │   ├── pdf_reader.py               纯标准库 PDF 解析（兜底）
│   │   ├── splitters.py                中文文本分割
│   │   ├── embedder.py                 离线哈希向量
│   │   ├── store.py                    向量库（Chroma 优先 / numpy 兜底）
│   │   ├── retriever.py                混合检索（BM25 + 向量）
│   │   ├── generator.py                提示词 + 生成 + 抽取式兜底
│   │   ├── rag.py                      RAG 主流程
│   │   ├── pipeline.py                 建库流水线（命令行与网页共用）
│   │   ├── profiles.py                 API 配置档案（增删改查 + 测试）
│   │   ├── chats.py                    对话存储
│   │   ├── sources.py                  外部目录登记
│   │   └── skips.py                    被过滤文件的记录
│   ├── agent\                          给其它 Agent 调用
│   │   ├── rag_client.py               Python / 命令行客户端
│   │   ├── langchain_tool.py           LangChain 工具封装
│   │   ├── mcp_server.py               MCP 服务（stdio）
│   │   └── openai_tool.json            function-calling schema
│   └── tools\                          测试与诊断（20 个脚本，见 src\README.md）
│
├── data\                               ← 你的资料放这里（pdf/docx/txt/md/csv/xlsx/json）
├── store\                              ← 索引产物（向量库），删掉重跑即可重建
├── config\                             ← API 配置 / 对话历史 / 跳过记录
├── dev-data\                           ← 开发调试截图，不参与检索
└── .venv\                              ← Python 环境
```

## 三、三种用法

### 1. 双击 bat（最省事）

| 文件 | 作用 |
|---|---|
| `0-打开网页.bat` | 服务在就直接开浏览器，不在就先启动再开 |
| `8-后台启动.bat` | **推荐**：把服务交给 Windows 计划任务托管，关终端/退出编辑器都不影响；日志写 `server.log` |
| `9-停止服务.bat` | 按端口停掉后台服务 |
| `1-建库.bat` | 建立/更新索引，等价于 `python ingest.py` |
| `2-提问.bat` | 命令行问答，等价于 `python ask.py` |
| `3-网页版.bat` | 起服务并打开问答页（服务已在跑时不会重复启动，只打开页面） |
| `4-API配置.bat` | 起服务并直接打开 **API 配置页** `/config` |
| `5-打开资料文件夹.bat` | 打开 `data\` 目录，往里丢文件 |
| `6-资料自动同步.bat` | 常驻监听 `data\`，文件一变就自动入库 |
| `7-诊断.bat` | 打不开时先跑它：端口/HTTP/代理/索引一次查完 |

### 2. 命令行

```bat
cd /d E:\RAG-KnowledgeBase

:: 建库（--reset 表示清空重建）
.venv\Scripts\python.exe src\ingest.py --reset

:: 单次提问
.venv\Scripts\python.exe src\ask.py "什么是向量数据库？"

:: 连续对话
.venv\Scripts\python.exe src\ask.py

:: 只检索不生成（调优时最有用）
.venv\Scripts\python.exe src\ask.py --retrieve-only "chunk_size 默认值"
```

### 3. 网页版

```bat
.venv\Scripts\python.exe src\web.py
```

打开 `http://127.0.0.1:8000`，输入问题即可。页面上可以直接调召回数量、
切换"用大模型生成"，每条答案下面列出命中原文和页码。

---

## 四、把回答升级成"真正的大模型生成"

网页上有专门的 **API 配置中心**（`http://127.0.0.1:8000/config`），可以新增多套配置、
随时启用、改完立即生效、一键做连通性测试、换掉不用的配置。详见文末「API 配置中心」一节。

也可以直接改根目录 `.env`：

**方案 A：阿里云百炼**（教程用的方案，有免费额度）

```ini
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-你的Key
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v1
```

**方案 B：DeepSeek**

```ini
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-你的Key
LLM_MODEL=deepseek-chat
```

**方案 C：本地 Ollama**（先装 Ollama 并 `ollama pull qwen3:4b`）

```ini
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:4b
USE_OLLAMA_EMBEDDING=1
OLLAMA_EMBED_MODEL=qwen3-embedding:4b
```

改完 `.env` 要**重新建库**（因为嵌入模型变了）：

```bat
.venv\Scripts\python.exe src\ingest.py --reset
```

改完 `.env` 先自检，确认 Key 真的通：

```bat
.venv\Scripts\python.exe src\tools\check_llm.py
```

它会打印地址/模型（Key 打码）并发一次最小请求，成功会显示模型回复，失败会直接告诉你
是 Key 无效（401）、余额不足（402）还是模型名写错（404）。

> 只有**换嵌入模型**才需要 `ingest.py --reset` 重建索引。只加对话 Key（DeepSeek / 百炼
> 对话）时，索引不用动。

> **DeepSeek 注意**：DeepSeek 平台只提供对话模型（`deepseek-chat` / `deepseek-reasoner`），
> **没有 embedding 接口**。所以用 DeepSeek 时，嵌入仍然是内置的离线哈希向量（词面相似），
> 检索能用但不是语义级。想同时升级检索精度，再加一个 `DASHSCOPE_API_KEY` 用
> `text-embedding-v1`（此时才需要重建索引）。

> 没配 `DASHSCOPE_API_KEY` 时，嵌入用的是内置的离线哈希向量（词面相似，
> 不懂同义词改写）。这是没有网络/没有额度情况下的可用降级方案，不是最优解。

---

## 五、加入自己的资料

有四种方式，按省事程度排：

### 1. 直接添加整个文件夹（不用复制）

问答页左侧「资料」区有三个按钮：

| 按钮 | 做什么 |
|---|---|
| **选文件** | 选一个或多个文件上传（复制进 `data\`） |
| **选文件夹** | 选一个文件夹，**保留子目录结构**全部上传（复制进 `data\<文件夹名>\`） |
| **填路径** | 粘贴本机任意文件夹的绝对路径，**不复制文件**，直接读原位置入库 |

- **拖拽**：把文件**或整个文件夹**拖到浏览器窗口任意位置，松手即入库（用了
  `webkitGetAsEntry` 递归遍历，子目录会保留）。
- 来源里会带上相对路径（如 `差旅制度资料/子目录/交通.txt`），方便在出处里核对。
- 一次传多个文件时走批量模式：先只落盘，最后一次统一建库，快很多。

也可以用接口直接调：

```bat
:: 导入文件夹，不复制
curl -X POST http://127.0.0.1:8000/api/import_folder ^
     -H "Content-Type: application/json" ^
     -d "{\"path\": \"D:\\\\资料\\\\产品文档\", \"copy\": false}"
```

`copy: true` 则复制进 `data\` 再入库。

### 2. 网页里拖文件进去

打开问答页，把文件拖到窗口任意位置 → 「松手即可加入知识库」→ 自动上传、切块、入库。

### 3. 丢进文件夹，自动同步

双击 `6-资料自动同步.bat`，它会一直盯着 `data\` 目录：往里复制文件，**2 秒内自动入库**，
控制台会打印切了多少块。适合长期往库里加东西。

双击 `5-打开资料文件夹.bat` 可直接打开 `data\` 目录。

> 同步是增量的：新增/修改会入库，但从目录删掉文件**不会**自动清理旧索引（需要重建）。

### 4. 命令行一次性重建

```bat
.venv\Scripts\python.exe src\ingest.py --reset
```

`--reset` 会清空旧索引再全量重建，适合大规模整理之后做一次收尾。

> **自动过滤**：日志、临时文件、校验清单不会被吞进知识库——
> `.log/.tmp/.bak/.lock/.pyc/.min/.map` 直接跳过；文件名含 `md5/checksum` 跳过；
> 单个文件 > 50MB 跳过；纯文本（txt/md/csv）> 2MB 视为日志跳过。
> 导入文件夹时会报告"跳过 N 个"及原因。

> **移除资料**：资料列表每行右侧有 `×`，点了会删掉该文件并重建索引
> （弹窗二次确认）。只想删掉某一批就逐条点，比全量重建省事。

### 支持格式与加载器

| 格式 | 加载器 | 说明 |
|---|---|---|
| pdf | PyPDFLoader（无 pypdf 时用内置解析器） | 一页一个 Document，再切块 |
| docx | python-docx | 段落 + 表格文本 |
| md / markdown | 内置 | 可按 `#`/`##` 标题切分 |
| txt | 内置 | UTF-8 / GBK 自适应 |
| csv | 内置 | **一行一个 Document**，适合 FAQ |
| xlsx | openpyxl | 一个工作表一个 Document |
| json | 内置 | 数组里每条一个 Document |

---

## 六、对话管理（问答页）

问答页左侧就是对话列表，行为和常见聊天应用一致：

| 操作 | 怎么做 |
|---|---|
| **新建对话** | 点左侧「＋ 新建对话」，右侧清空进入欢迎页（带 6 个示例问题） |
| **自动保存** | 每次提问后，你的问题和 AI 回答（含出处、模式）自动落盘，标题取第一条提问 |
| **恢复历史** | 点左侧任意对话，右侧按顺序还原全部消息和出处卡片 |
| **重命名** | 双击对话标题，输入新名字 |
| **删除** | 鼠标移到对话上，点右侧 `×`，二次确认 |

**回答里的出处默认是收起的**：每条回答下面只有一行 `▸ 参考资料 · N 段`，
点它（或点箭头）才展开原文片段和相似度。这样一屏能放下更多对话，
需要核对时再展开。

存储位置：`config\chats\<会话id>.json`，一个会话一个文件，纯文本可直接备份。
页面顶部的副标题会显示「N 条消息 · 自动保存」。

> 不建对话也能直接用：没选中会话时提问，会自动新建一个并保存。

---

## 七、资料库管理（网页）

访问 `http://127.0.0.1:8000/library`，或点左侧导航「资料库」。

```
资料库
┌ 文件 2 个 │ 外部目录 0 个 │ 分块 194 │ 总字数 7.4万 │ 后端 chroma │ 嵌入 离线哈希向量 ┐

[搜索文件名…]                    [上传文件] [导入文件夹] [填本机路径] [重建索引]

┌──┬────────────────────────┬──────┬────────┬──────┬───────┬──────────────┬──────────┐
│☐ │ 名称                    │ 类型 │ 大小   │ 分块 │ 字数  │ 加入时间      │ 操作      │
├──┼────────────────────────┼──────┼────────┼──────┼───────┼──────────────┼──────────┤
│☐ │ LangChain-RAG-Agent…pdf │ PDF  │ 31.2MB │ 191  │ 7.2万 │ 10-20 15:19  │ 预览 删除 │
│☐ │ 使用说明-FAQ.md         │ MD   │ 3 KB   │ 3    │ 1391  │ 10-20 16:47  │ 预览 删除 │
└──┴────────────────────────┴──────┴────────┴──────┴───────┴──────────────┴──────────┘
```

能做的事：

| 功能 | 说明 |
|---|---|
| **看分块数** | 每行显示它实际贡献多少检索单元——日志类文件会异常大，一眼就能发现 |
| **预览** | 点开看该文件前几段分块原文（带页码），确认解析正常、没把乱码吞进去 |
| **删除** | 单行「删除」；data 里的文件会被删除，外部目录只取消登记（原文件不动） |
| **批量删除** | 勾选多行 → 底部出现操作条 → 批量删除 |
| **搜索** | 按文件名过滤 |
| **上传 / 导入** | 上传文件、导入文件夹（保留子目录）、填本机路径（不复制）都在这一页 |
| **重建索引** | 清空后全量重建；索引残留（文件已删但块还在）也会在这步被清掉 |

**三类条目**（表格「类型」列）：

- `PDF/MD/...` —— `data\` 目录里的真实文件
- `外部目录` —— 用「填本机路径」导入的文件夹，**只登记不复制**；路径记在
  `config\external_sources.json`，重建索引时会一起读回来
- `索引残留` —— 文件已不在，但旧分块还留在库里，点「重建索引」清掉

> 分块数异常大（比如几千）通常意味着把日志或压缩包里的文本吞进去了。
> 先「预览」看看内容，不对就删掉——删完索引会自动重建。

---

## 八、参数怎么调

在 `src/ragkb/config.py` 顶部，或建库时用命令行参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `CHUNK_SIZE` | 500 | 每块字数。答案被切断→调大；召回太杂→调小 |
| `CHUNK_OVERLAP` | 50 | 相邻块重叠，一般取 chunk_size 的 10% |
| `TOP_K` | 4 | 召回条数。缺细节→6~8；噪声多→2~3 |
| `W_BM25` / `W_VEC` | 0.55 / 0.45 | 关键词分与向量分的权重 |
| `EMBED_DIM` | 4096 | 离线哈希向量维度 |

```bat
:: 长文档建议：更大的块、更大的重叠
.venv\Scripts\python.exe src\ingest.py --reset --chunk-size 800 --overlap 80
```

---

## 九、检索结果不准怎么办

**先分清是"没召回"还是"召回了没用上"**：

```bat
:: 只看检索，不看生成
.venv\Scripts\python.exe src\ask.py --retrieve-only "你的问题"
```

- 命中的片段里**根本没有答案** → 分块或嵌入模型的问题。调 `--chunk-size`，
  确认文档本身包含答案，必要时换嵌入模型后 `--reset` 重建。
- 命中的片段里**有答案但回答错** → 提示词或 Top-K 的问题。调大 `-k`，
  检查 `generator.py` 里 `PROMPT_TEMPLATE` 的反幻觉约束。
- 只在某个文件里找 → `--source 文件名` 限定检索范围。

---

## 十、和教程的对应关系

| 教程内容 | 本项目的实现 |
|---|---|
| P3-P5 RAG 原理、两阶段、五组件 | `README` 与 `rag.py` 的流程 |
| P10-P14 百炼 API Key | `.env` 的 `DASHSCOPE_API_KEY` |
| P15-P23 Ollama 本地模型 | `.env` 的 `LLM_PROVIDER=ollama` |
| P44 嵌入模型 | `src/ragkb/embedder.py`（DashScope 或离线哈希） |
| P60-P70 文档加载器 | `src/ragkb/loaders.py` |
| P71-P76 文本分割器 | `src/ragkb/splitters.py` |
| P77-P79 向量存储与检索 | `src/ragkb/store.py` + `retriever.py` |
| P80-P83 RetrievalQA | `src/ragkb/rag.py`（检索→增强→生成） |

比教程多做的两件事：

1. **混合检索**：向量分 + BM25 关键词分融合，并对链接清单块、代码块降权，
   同一页只保留最相关的一块。教程里是纯向量检索，中文专有名词容易翻车。
2. **离线降级**：没有网络或没有 API Key 时，用哈希向量 + 抽取式回答，
   保证知识库永远是能用的状态，而不是一堆报错。

### 到底用到了 LangChain 的哪几处（这是刻意取舍，不是漏了）

装是装全了（`langchain` / `langchain-chroma` / `langchain-community` /
`langchain-text-splitters` / `langchain-ollama`），但**运行路径上只用了三处**：

| 环节 | 实现 | 归属 |
|---|---|---|
| 向量库 | `langchain_chroma.Chroma` + `langchain_core.documents.Document` | **LangChain** |
| 嵌入模型 | `DashScopeEmbeddings`（百炼）/ `OllamaEmbeddings`（本地） | **LangChain** |
| Agent 工具 | `langchain_core.tools.tool`（`agent/langchain_tool.py`） | **LangChain** |
| 文档加载 | `src/ragkb/loaders.py` + 纯标准库 PDF 解析 | 自研 |
| 文本分割 | `src/ragkb/splitters.py` | 自研 |
| 检索 | `src/ragkb/retriever.py`（BM25 + 向量融合） | 自研 |
| 生成 | `src/ragkb/generator.py`（`urllib` 调 `/chat/completions`） | 自研 |

为什么不全量套用课件写法：

1. **起点约束**：最初这台机器没有 Python、没有网络，先写了零依赖的可用版本；
   能装依赖之后，只把"最值得用 LangChain"的部分（Chroma、嵌入模型）接进来。
2. **效果优先**：课件里 `RetrievalQA + 纯向量检索` 在中文课件上会退化
   （实测 `电脑` ↔ `计算机` 相似度 0，见 `tools/demo_embedding.py`），
   所以检索层换成混合检索，分块也按中文标点重写了。
3. **可控性**：反幻觉提示词、出处编号、离线兜底、Top-K 去重，自己拼比套 `RetrievalQA`
   更容易调。

想对照课件原版写法的，可以把 `src/ragkb/` 里的对应模块换成 `PyPDFLoader` /
`RecursiveCharacterTextSplitter` / `as_retriever()` / `RetrievalQA`——接口是等价的，
但上面两点收益会丢。

---

## 十一、常见问题

**Q：浏览器输入 http://127.0.0.1:8000/ 打不开？**

先跑 `7-诊断.bat`（或 `service_task.py status`）。三种常见情况：

| 现象 | 原因 | 处理 |
|---|---|---|
| 端口没人监听 | 服务没起来 | 双击 `8-后台启动.bat` |
| 端口被占但页面打不开 | 浏览器走了代理/HTTPS | 地址必须是 `http://`（不是 https）；关掉代理或把 `127.0.0.1` 加入直连 |
| 提示连接被拒绝 | 服务进程挂了 | `8-后台启动.bat` 重新拉起 |

> 服务现在由**计划任务**（`RAG-KnowledgeBase`）托管，不再依赖任何终端窗口。
> 命令：`python src\tools\service_task.py status|start|stop`。


**Q：文件放进去了，怎么没入库？**

去「资料库」页看顶部的黄色横幅 **最近跳过的文件**，那里会列出来并写明原因。
被过滤的规则（都在 `ragkb\loaders.py` 里）：

| 规则 | 触发例子 |
|---|---|
| 后缀黑名单 | `.log` `.tmp` `.bak` `.lock` `.pyc` `.min` `.map` |
| 文件名像日志 | `JLinkLog.txt`、`build.txt`（文件名以 log 结尾） |
| 内容是日志 | ≥100KB 且多数行以时间戳开头（`02:11:47`、`2026-10-20`） |
| 校验清单 | 文件名含 `md5` / `checksum` |
| 纯文本过大 | txt/md/csv 超过 0.5MB |
| 单文件过大 | 超过 50MB |

被跳过的文件在表格里也会显示一行，类型标成「已跳过」，分块数是 0——
**能看见，就不会再有"我明明放进去了"的困惑**。确认要收录的话，把文件另存成
正常的 markdown / docx 再放进去即可。

**Q：`1-建库.bat` 一闪而过？**
在文件所在目录按住 Shift 右键 → 在此处打开 PowerShell，手动运行
`.venv\Scripts\python.exe src\ingest.py`，看完整报错。

**Q：`store\` 可以删吗？**
可以，删掉后重新建库即可，原始文档都在 `data\` 里。

**Q：数据会上传吗？**
建库和检索都在本机。只有配置了大模型并启用生成时，命中的片段才会随提示词
发给对应服务商。不配 Key 时全程不出本机。

**Q：浏览器打不开 `http://localhost:8000`？**

**先双击 `7-诊断.bat`**，它会在系统层面（不依赖浏览器）检查端口、HTTP、系统代理、
索引和配置，然后直接告诉你结论。典型输出：

```
✅ 127.0.0.1:8000 监听        ✅ HTTP 200
✅ [::1]:8000 监听            ✅ 系统代理：关闭
✅ 索引 194 块 / 2 文件       ✅ API 配置 1 套
→ 服务完全正常，问题在浏览器侧
```

按这个顺序排查：

1. 地址用 `http://127.0.0.1:8000/`——别用 `https://`，别用 `localhost`（代理场景下
   `localhost` 更容易被拦）。
2. 双击 `0-打开网页.bat`：它会自己判断服务是否在跑，该起服务就起，然后打开浏览器。
3. 关掉 Clash / VPN 的系统代理，或把 `127.0.0.1`、`localhost` 加进代理绕过列表。
   诊断脚本会读出代理开关和绕过列表，没绕过会标 ⚠。
4. 换浏览器或无痕窗口试一次，排除缓存/扩展影响。
5. 服务确实没起来时再双击 `3-网页版.bat`，**那个控制台窗口别关**——它就是服务本体。

**Q：双击 bat 后浏览器显示"无法访问此网站"？**

旧版 bat 是先开浏览器再起服务，浏览器抢跑就会这样。现在 bat 用 `--open` 参数，
服务绑定成功后才打开浏览器（延迟 1 秒），不会再抢跑。

**Q：想用手机/别的电脑访问？**

```bat
.venv\Scripts\python.exe src\web.py --host 0.0.0.0
```

然后用本机局域网 IP 访问（`ipconfig` 查，例如 `http://172.22.124.143:8000`）。
注意这会暴露到局域网，默认只监听本机回环。

**Q：换电脑能用吗？**
整个文件夹可以拷走，但 `.venv` 里的 Python 路径是写死的，换机器要在那边重建
虚拟环境：`python -m venv .venv` + `pip install -r requirements.txt`。

---

## 十二、让别人也能用（问答免口令，管理要口令）

服务监听 `0.0.0.0`，同一网络里的设备可以直接访问。**问答案不需要任何口令。**

| 谁 | 地址 | 体验 |
|---|---|---|
| 你自己 | http://127.0.0.1:8000/ | 全部功能免密（本机自动是管理员） |
| 同事（同 WiFi） | http://172.22.124.143:8000/ | 打开即用：提问、看历史、浏览资料 |
| 同事（Radmin VPN） | http://26.94.195.90:8000/ | 同上（对方需装 Radmin 并加入网络） |

### 右上角身份与登录

三个页面的右上角都有**身份徽标 + 按钮**：

| 身份 | 徽标 | 按钮 | 说明 |
|---|---|---|---|
| 本机 | 蓝色「本机管理员」 | 退出登录 | 你自己，免密全套权限 |
| 远程已登录 | 绿色「管理员」 | 退出登录 | 输过口令 |
| 远程未登录 | 灰色「访客」 | 管理员登录 | 问答随便用 |

访客点「API 配置」（或直接开 `/config`）会跳到「管理口令」登录页，登录成功后自动跳回配置页。
访客在资料库里：只有「预览」，上传 / 导入 / 删除 / 重建索引按钮全部隐藏，勾选列也不显示。

### 权限边界

| 操作 | 谁都能做 | 需要管理口令 |
|---|---|---|
| 问答 / 检索 / 看历史对话 | ✅ | |
| 浏览资料库（列表、预览分块） | ✅ | |
| 改 API 配置 / 换模型 | | ✅ |
| 重建索引 | | ✅ |
| 上传文件 / 导入外部目录 | | ✅ |
| 删除资料 / 清空跳过记录 | | ✅ |

点侧栏「管理登录」或直接开 `/config`，会跳到登录页；输一次口令，7 天内有效。
口令在启动日志里能看到：

```
  给别人用 : http://172.22.124.143:8000/
  访问口令 : kb-1b0b0f（管理功能需要）
```

### 安全细节

- **登录页不泄露信息**：只有标题、说明和输入框。
- **防暴力破解**：同一 IP 10 分钟内错 5 次，锁 60 秒（第 6 次返回 429，期间正确口令也不放行）。
  按 5 次/分钟算，16^6 种组合要试十几年。
- **管理接口不带口令一律 401**：`/api/reindex`、`/api/profiles`、`DELETE /api/files`、`/api/upload` 等。
- **局限**：HTTP 明文传输，同一局域网内能看到别人登录后的 cookie（可重放 7 天）。
  适合家里/公司内网，不适合公共 WiFi。

### 改口令（在网页里改，不用碰文件）

打开 **http://127.0.0.1:8000/config**，页面底部有「访问口令」卡片：

| 控件 | 作用 |
|---|---|
| 当前 / 新口令 | 直接显示现在的口令，改成新的即可（留空=不改） |
| 登录有效期（天） | 输一次口令后多少天免输，1–90 |
| 启用管理口令 | 关掉后谁都能改配置、删资料（不建议） |

保存后**旧登录全部失效**（签名密钥会轮换），已登录的人需要用新口令重新登录。
改口令不需要重启服务。

### 用命令行改（备选）

```bat
:: 改口令：编辑 config\access.json 的 password 字段，然后重启（9- → 8-）
:: 想让管理功能也免口令（同网段任何人可删资料，不建议）：
.venv\Scripts\python.exe -c "import sys;sys.path.insert(0,r'src');from ragkb import access;access.set_enabled(False)"
```

### 防火墙

这台机器 Windows 防火墙「专用/公用」是关闭状态，局域网可直接连，无需放行。
若哪天打开了防火墙，管理员权限执行：

```powershell
New-NetFirewallRule -DisplayName "RAG-KnowledgeBase 8000" -Direction Inbound `
  -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private,Domain
```

---

## 十三、给其它 Agent 调用

知识库跑起来之后就是一个本地 HTTP 服务，任何 agent 都能把它当工具用。
详细示例见 [`agent/README.md`](agent/README.md)，这里给最常用的三种：

**① HTTP（任何语言）**

```bash
curl -X POST http://127.0.0.1:8000/api/ask ^
     -H "Content-Type: application/json" ^
     -d "{\"question\": \"什么是向量数据库\", \"k\": 4}"
```

**② Python 客户端**

```python
import sys; sys.path.insert(0, r"E:\RAG-KnowledgeBase\agent")
from rag_client import RAGClient
kb = RAGClient()
print(kb.ask("公司差旅住宿标准是多少？")["answer"])
```

**③ MCP 服务（Claude Desktop / Cursor / 百炼）**

```json
{"mcpServers": {"rag-knowledge-base": {
  "command": "E:/RAG-KnowledgeBase/.venv/Scripts/python.exe",
  "args": ["E:/RAG-KnowledgeBase/agent/mcp_server.py"]}}}
```

`agent/` 目录里还有 LangChain 工具封装（`langchain_tool.py`）和 OpenAI function-calling
的 schema（`openai_tool.json`）。自测：

```bat
.venv\Scripts\python.exe src\src\tools\test_agent_api.py 8000
```

---

## 十四、本地模型（已装好，全在 E 盘，不依赖外网）

Ollama 的程序和模型**都搬到了 E 盘**，C 盘只留一个空壳注册项：

```
E:\RAG-KnowledgeBase\ollama\
├── app\        2.9 GB   Ollama 0.40.6 程序（含 CUDA 库）
└── models\     1.1 GB   模型仓库（qwen-local）

环境变量 OLLAMA_MODELS = E:\RAG-KnowledgeBase\ollama\models
启动方式   按需启动：只在「当前启用本地模型」时，随知识库一起拉起（已取消开机自启）
服务       http://localhost:11434/v1（OpenAI 兼容）
知识库档案 「本地模型（Qwen2.5-1.5B）」= qwen-local，已启用
实测       RTX 4060 Laptop 独显推理，43 tokens / 0.2 秒
```

### 为什么不是 `ollama pull`

**拉不动。** 实测 `registry.ollama.ai` 的模型文件只有 5 KB/s（8 MB 花了 1608 秒）。
所以模型从**魔搭（ModelScope）**下 GGUF（2~3 MB/s，8 分钟），再用 `ollama create` 本地导入：

```bat
.venv\Scripts\python.exe src\tools\fetch_gguf.py                      :: 1) 魔搭下 GGUF
ollama create qwen-local -f models\Modelfile                             :: 2) 导入（不联网）
.venv\Scripts\python.exe src\tools\setup_local_model.py               :: 3) 建档案并启用
.venv\Scripts\python.exe src\tools\move_ollama_to_e.py                :: 需要时再搬目录
```

### 按需启动，不常驻

**不开机自启**（`Startup\Ollama.lnk` 已删除）。规则很简单：

| 当前启用的档案 | 启动知识库时 |
|---|---|
| 本地模型（qwen-local） | 自动把 Ollama 拉起来（`ollama serve`，无托盘、无窗口） |
| DeepSeek / 百炼等云端 | **完全不碰 Ollama**，一个进程都不多 |

停止知识库（`9-停止服务.bat`）时，本地模型也一起停，内存立刻释放。

想单独控制本地模型：`11-启动检查本地模型.bat`（先看状态 → 需要才启动 → 再看状态）。

> 注意：别去点 Ollama 的托盘程序（`ollama app.exe`），它会自己把开机自启加回来。
> 我们用的是 `ollama serve`，够用且安静。

### 日常

| 要做的事 | 怎么做 |
|---|---|
| 启动/查看本地模型 | 双击 `11-启动检查本地模型.bat` |
| 切回云端 | 配置页点「DeepSeek 官方」→「启用」，索引不用重建 |
| 换模型 | 改 `models\Modelfile` 的 `FROM`，重跑 `ollama create` |
| 删冗余 | `models\*.gguf`（1.1 GB）是导入源副本，Ollama 已另存，可删 |

---

## 十五、API 配置中心（网页）

打开方式：双击 `4-API配置.bat`，或访问 `http://127.0.0.1:8000/config`。

### 界面布局（左右分区）

```
┌───────────────┬──────────────────────────────────────────────┐
│ 品牌 / 导航    │  主区标题                                    │
├───────────────┼──────────────────────────────────────────────┤
│ 配置列表       │  选中配置的详情表单                          │
│ · DeepSeek    │   名称 / 服务商 / Base URL / 模型 / Key       │
│ · 百炼        │   嵌入方式 / 嵌入模型                          │
│ + 新增        │   [保存修改] [启用] [测试连通性]     [删除]   │
│               ├──────────────────────────────────────────────┤
│ 索引状态       │  当前状态卡（索引块数 / 后端 / 嵌入 / 启用项）│
│ [重建索引]     │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

- **左侧栏固定 292px**：上半是导航和配置列表（点条目即切换右侧详情，绿点=当前启用），
  底部常驻索引状态和「重建索引」按钮，滚动只发生在右侧。
- **右侧主区**：配置页是"选中项的详情 + 当前状态"；问答页是对话流 + 底部输入框。
- 窗口窄于 1000px 时左栏仍固定，右侧内容自适应。
- **点「+ 新增」时表单已经预填好**：默认服务商 DeepSeek，名称 / Base URL / 模型名都带出来，
  只需粘 Key 就能保存。换服务商这三项会跟着变（除非你手动改过名称）。
- **选服务商时**：Base URL、模型名、名称会一起跟着变。名称只在"你没手动改过"时才跟随——
  一旦你手动输入过，就保持你的命名，不会被切服务商覆盖；把名称清空后又恢复跟随。

### 能做的事

| 操作 | 说明 |
|---|---|
| **新增** | 左侧「+ 新增」→ 右侧出现空白表单；选服务商会自动带出 Base URL、模型名和**名称** |
| **修改** | 直接在右侧改；Key 输入框留空表示保持原 Key 不变 |
| **删除** | 右下「删除」，二次确认；删的是启用中那套会自动切到剩下的第一套 |
| **启用** | 「启用这套」立刻生效，问答页刷新即用新模型 |
| **测试** | 真的发一次最小请求，把 401/402/404 翻译成中文原因，结果显示在表单下方 |
| **重建索引** | 换过「嵌入方式」会亮黄条提示，点左下角按钮就地重建 |

支持的服务商预设：DeepSeek、阿里云百炼、OpenAI、本地 Ollama、任意 OpenAI 兼容服务。

**存储位置**：`config\llm_profiles.json`。Key 以明文保存在这个本机文件里，
网页只回显掩码（`sk-ab****wxyz`），接口不会把明文 Key 回传给浏览器。

**嵌入方式有三种**（页面上每个配置单独选）：

| 选项 | 需要 Key | 特点 |
|---|---|---|
| 离线哈希向量 | 否 | 开箱可用，词面相似，不懂同义词改写 |
| 百炼 text-embedding | 是 | 语义级检索，中文效果好；换它必须重建索引 |
| 本地 Ollama 嵌入 | 否（要装 Ollama） | 语义级且离线，模型较大 |

### 嵌入模型到底在干什么

**把一段文字变成一串数字（向量）**，让"意思相近的文字，向量也靠得近"。
它在 RAG 里只负责**检索**这一步（找到相关片段），不负责回答问题——
回答问题的是对话模型。两者可以来自不同服务商。

为什么需要它：知识库可能有几十万字，不可能每次提问都把全文塞给模型。
先把每块文本算成向量存进库，提问时只把"最像的几块"取出来给模型，才有意义。

本项目的离线哈希向量算的是**字面重合度**，不是语义。用
`src\tools\demo_embedding.py` 可以看到真实数字：

```
0.000  电脑坏了怎么办  ↔  计算机故障如何处理      ← 同义，但一个字都不重合
0.000  RAG 是什么     ↔  检索增强生成是什么        ← 缩写 vs 全称，认不出
0.714  什么是向量数据库 ↔ 向量数据库是做什么的      ← 字面重合，认得
0.316  汽车轮胎怎么换  ↔  轿车轮胎的更换方法        ← 共享"轮胎"，部分认得
```

所以：不配嵌入模型也能用（还有 BM25 关键词分兜底），但提问方式和文档用词
差得远时容易召不回。换成 `text-embedding-v1` 这类真嵌入模型，就是为了让
"意思相近"能被认出来。

**换嵌入模型必须重建索引**：索引里存的是旧模型算出的向量，换了模型向量空间
就不是一套了。页面检测到不一致会亮黄条，点「重建索引」即可。

**优先级**：网页里启用的配置 > `.env` > 环境变量里探测到的 Key。所以配好网页后，
`.env` 就可以留空不用管了。

**接口一览**（自动化/二次开发可用）：

```
GET    /api/stats                   索引与模型状态
POST   /api/ask                     提问
GET    /api/profiles                配置列表（Key 打码）
POST   /api/profiles                新增
PUT    /api/profiles/{id}           修改
DELETE /api/profiles/{id}           删除
POST   /api/profiles/{id}/activate  启用
POST   /api/profiles/{id}/test      连通性测试
POST   /api/reindex                 重建索引
POST   /api/upload?name=文件名      上传一个文件并入库（body 为文件原始字节；?index=0 只存不建库）
POST   /api/import_folder           导入本机一个文件夹 {"path": "D:\\资料", "copy": false}
GET    /api/files                   资料清单（文件名/大小/修改时间，含子目录）
POST   /api/selftest_result         仅开发用：浏览器自测结果回传
```

自检脚本（不需要浏览器）：

```bat
.venv\Scripts\python.exe src\src\tools\test_web.py 8000      :: CRUD + 测试 + 问答 冒烟测试
.venv\Scripts\python.exe src\src\tools\test_web2.py 8000     :: 重建索引 + 嵌入不一致告警
.venv\Scripts\python.exe src\src\tools\test_ui.py 8000       :: 布局与元素结构检查
.venv\Scripts\python.exe src\src\tools\test_ui_flow.py 8000  :: 无头浏览器真实点击：名称跟随
.venv\Scripts\python.exe src\src\tools\test_upload.py 8000   :: 单文件上传入库
.venv\Scripts\python.exe src\src\tools\test_folder.py 8000   :: 整个文件夹导入
.venv\Scripts\python.exe src\src\tools\test_filter.py 8000   :: 噪声过滤 + 单个资料删除
.venv\Scripts\python.exe src\src\tools\test_library.py 8000  :: 资料库列表 / 预览 / 外部目录登记
.venv\Scripts\python.exe src\src\tools\test_chats.py 8000    :: 对话保存 / 新建 / 恢复
.venv\Scripts\python.exe src\tools\check_js.py 8000      :: 页面 JS 语法检查（改界面后必跑）
.venv\Scripts\python.exe src\tools\check_llm.py          :: 命令行自检当前启用的模型
```

> **`check_js.py` 为什么必须存在**：页面是写在 Python 字符串里的 HTML/JS，
> 在 JS 里写 `'\n'` 会先被 Python 解析成真换行，塞进单引号字符串就是语法错误——
> 服务端 Python 一切正常，只有浏览器里白屏或"卡在加载中"。
> 这个脚本用 `node --check` 校验两个页面抽出来的脚本，能在改完界面后立刻发现问题。
