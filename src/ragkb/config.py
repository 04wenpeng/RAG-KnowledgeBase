# -*- coding: utf-8 -*-
"""RAG 知识库 —— 全局配置。

参数取值对照课件：
  P72-P74  中文优化分隔符 + 递归分割
  P77-P79  Chroma 向量库（本项目离线自建，接口对齐）
  P80-P83  RetrievalQA 的 Top-K 与提示模板
"""
from pathlib import Path
import os
import sys

# ragkb/config.py -> ragkb -> src -> 项目根目录
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STORE_DIR = BASE_DIR / "store"

# ——— 分块（课件 P72-P74）———
CHUNK_SIZE = 500          # 中文 300~800 常用
CHUNK_OVERLAP = 50        # 一般取 chunk_size 的 10%
SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

# ——— 向量化（离线替代嵌入模型）———
EMBED_DIM = 4096
NGRAM_MIN, NGRAM_MAX = 2, 3

# ——— 检索 ———
TOP_K = 4
BM25_K1 = 1.5
BM25_B = 0.75
W_BM25 = 0.55             # 关键词分权重
W_VEC = 0.45              # 向量分权重
SUBSTRING_BONUS = 0.08    # 问题原串命中加分
MAX_CONTEXT_CHARS = 4000  # 喂给大模型的上下文上限
LLM_MAX_TOKENS = 600      # 单次回答上限；本地小模型更需要限制
LLM_TIMEOUT = 60          # 云端接口超时（秒）
LLM_TIMEOUT_LOCAL = 240   # 本地 CPU 推理慢，单独给更长的超时


def load_env() -> None:
    """读取项目根目录 .env（不依赖 python-dotenv）。"""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


load_env()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

# 兼容 OpenAI 协议的服务商预设（课件 P12-P23）
PRESETS = {
    "dashscope": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "DASHSCOPE_API_KEY"),
    "ollama": ("http://localhost:11434/v1", "qwen3:4b", ""),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini", "OPENAI_API_KEY"),
    "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat", "DEEPSEEK_API_KEY"),
}


def llm_config():
    """返回 (base_url, api_key, model)；未配置则 None（走离线抽取式回答）。

    优先级：网页里启用的 API 配置 > .env 里的配置 > 环境变量里探测到的 Key。
    """
    try:
        from .profiles import active_llm_config

        cfg = active_llm_config()
        if cfg:
            return cfg
    except Exception:
        pass

    provider = LLM_PROVIDER
    if provider in PRESETS:
        url, model, keyenv = PRESETS[provider]
        key = LLM_API_KEY or os.getenv(keyenv, "")
        if provider != "ollama" and not key:
            return None
        return (LLM_BASE_URL or url, key, LLM_MODEL or model)
    if LLM_BASE_URL and LLM_MODEL:
        return (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL)
    # 未显式配置时，自动探测环境里已有的 Key
    for provider, (url, model, keyenv) in PRESETS.items():
        key = os.getenv(keyenv, "")
        if key:
            return (url, key, model)
    return None


COLLECTION = "kb_docs"   # 相当于数据库表名（课件 P79）


_EMBEDDING_WARNING = ""      # 记录"想要的嵌入模型没启用成功"的原因


def embeddings_backend():
    """选嵌入模型：网页配置优先，其次 .env，最后退化为离线哈希向量。"""
    global _EMBEDDING_WARNING
    _EMBEDDING_WARNING = ""

    mode, model, key = "offline", "", ""
    try:
        from .profiles import active_embedding, active_profile

        if active_profile():
            mode, model, key = active_embedding()
        else:
            key = os.getenv("DASHSCOPE_API_KEY", "").strip()
            if key:
                mode, model = "dashscope", os.getenv("EMBEDDING_MODEL", "").strip()
            elif os.getenv("USE_OLLAMA_EMBEDDING", "") == "1":
                mode, model = "ollama", os.getenv("OLLAMA_EMBED_MODEL", "").strip()
    except Exception:
        key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        mode = "dashscope" if key else "offline"

    if mode == "dashscope":
        if not key:
            _EMBEDDING_WARNING = "配置里选了百炼嵌入，但没有可用的 Key，已退回离线哈希向量"
        else:
            try:
                from langchain_community.embeddings import DashScopeEmbeddings

                # 显式传 Key，不写进 os.environ，避免污染其它配置解析
                return DashScopeEmbeddings(
                    model=model or "text-embedding-v1",
                    dashscope_api_key=key,
                )
            except Exception as exc:
                _EMBEDDING_WARNING = f"百炼嵌入初始化失败（{type(exc).__name__}: {exc}），已退回离线哈希向量"

    if mode == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(model=model or "qwen3-embedding:4b")
        except Exception as exc:
            _EMBEDDING_WARNING = (
                f"本地 Ollama 嵌入不可用（{type(exc).__name__}: {exc}），已退回离线哈希向量"
            )

    from .embedder import HashingEmbedder

    return HashingEmbedder()


def embedding_warning() -> str:
    return _EMBEDDING_WARNING


def embedding_hint() -> str:
    """给人看的一句描述，用于控制台和网页。"""
    try:
        from .profiles import active_embedding, active_profile

        if active_profile():
            mode, model, key = active_embedding()
            if mode == "dashscope" and key:
                return f"百炼 {model or 'text-embedding-v1'}"
            if mode == "ollama":
                return f"Ollama {model or 'qwen3-embedding:4b'}"
            return "离线哈希向量（网页配置为离线模式）"
    except Exception:
        pass

    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if key:
        return f"DashScope {os.getenv('EMBEDDING_MODEL', 'text-embedding-v1')}"
    return "离线哈希向量（未配嵌入模型）"


def embedding_signature() -> str:
    """用于判断"索引是用哪个嵌入模型建的"。换模型必须重建索引。"""
    try:
        emb = embeddings_backend()
        return f"{getattr(emb, 'name', type(emb).__name__)}"
    except Exception:
        return "unknown"


def llm_label() -> str:
    cfg = llm_config()
    return f"{cfg[2]} @ {cfg[0]}" if cfg else ""


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def setup_stdio() -> None:
    """避免中文在 GBK 控制台里报 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
