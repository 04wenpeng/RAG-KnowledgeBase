# -*- coding: utf-8 -*-
"""生成模块：把检索结果变成答案（课件 P80-P83 的「增强 + 生成」两步）。

两种模式：
  1. llm        —— 配好 .env（百炼/OpenAI/Ollama/DeepSeek）就调大模型，真正 RAG
  2. extractive —— 没有大模型时，从命中片段里抽句子拼答案（离线可用，带出处）
提示词沿课件 P82 的反幻觉写法：找不到就明说，不许编。
"""
from __future__ import annotations

import json
import re
import urllib.request

from .config import (
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    LLM_TIMEOUT_LOCAL,
    MAX_CONTEXT_CHARS,
    llm_config,
)

PROMPT_TEMPLATE = """你是资料问答助手。下面是检索到的资料片段，请据此回答用户的问题。

要求：
1. 优先从资料里找答案。只要资料中出现相关数值、名称、定义或步骤，就直接给出，并在句末用 [1][2] 标注出处编号。
2. 用户的说法与资料措辞不完全一致也算命中（例如“默认是多少”对应资料里的“默认值”）。不要因为用词不同就说无法回答。
2b. 答案尽量出自同一份资料里相邻的段落；资料是步骤时按原顺序列出，不要把不同资料里的步骤拼在一起。
3. 只有在资料确实完全没有相关内容时，才回答"根据现有资料无法回答这个问题"，不要编造。
4. 回答简洁、可直接使用；能列点就列点。

资料：
{context}

问题：
{question}

回答："""


def build_context(hits: list[dict], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """把命中片段编号拼成上下文（对应 RetrievalQA 的 stuff 模式）。"""
    parts, used = [], 0
    for i, hit in enumerate(hits, 1):
        meta = hit.get("metadata", {}) or {}
        loc = []
        if meta.get("page"):
            loc.append(f"第{meta['page']}页")
        if meta.get("row") is not None:
            loc.append(f"第{int(meta['row']) + 1}行")
        if meta.get("sheet"):
            loc.append(str(meta["sheet"]))
        label = f"[{i}] {meta.get('source', '资料')}" + (f"（{'，'.join(loc)}）" if loc else "")
        block = f"{label}\n{hit['content']}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def build_prompt(question: str, hits: list[dict]) -> str:
    return PROMPT_TEMPLATE.format(context=build_context(hits), question=question)


# ————————————————————— 大模型调用 —————————————————————
def call_llm(prompt: str, timeout: int | None = None) -> str:
    cfg = llm_config()
    if not cfg:
        raise RuntimeError("未配置大模型")
    base_url, api_key, model = cfg
    if timeout is None:
        # 本机服务（Ollama / llama.cpp）给更长的超时，CPU 推理就是慢
        local = any(h in base_url for h in ("127.0.0.1", "localhost", "::1"))
        timeout = LLM_TIMEOUT_LOCAL if local else LLM_TIMEOUT
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system",
             "content": "你是严谨的企业知识库问答助手，只依据给定的已知信息回答。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": LLM_MAX_TOKENS,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


# ————————————————————— 离线抽取式回答 —————————————————————
_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;])")
_BAD_TAIL = ("（", "(", "、", "，", ",", "：", ":", "的", "和", "与")
_LEAD_PUNCT = "）)。，、；：,.;: "


def _norm(text: str) -> str:
    """PDF 抽出来的文本里有大量软换行，先压平再断句。"""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _candidates(text: str, max_len: int = 400, win: int = 200, step: int = 120) -> list[str]:
    """把片段切成候选句子；超长的表格行再滑窗，避免答案被长度过滤掉。"""
    norm = _norm(text)
    out: list[str] = []
    for piece in _SENT_SPLIT.split(norm):
        s = (piece or "").strip().lstrip(_LEAD_PUNCT)
        if len(s) < 14:
            continue
        if len(s) <= max_len:
            out.append(s)
        else:
            for i in range(0, max(1, len(s) - win + 1), step):
                out.append(s[i:i + win])
            out.append(s[-win:])
    return out


_CODE_MARKERS = ("import ", "def ", "print(", "return ", " = ", "self.", ".py", "()", "# ")


def _looks_code(text: str) -> bool:
    """代码行光看括号占比不够（中文注释会稀释），再看关键词个数。"""
    hits = sum(1 for m in _CODE_MARKERS if m in text)
    return hits >= 2


def extractive_answer(question: str, hits: list[dict], max_sentences: int = 4,
                      idf: dict[str, float] | None = None) -> str:
    from .embedder import code_ratio, terms

    q_terms = list(dict.fromkeys(terms(question)))
    q_set = set(q_terms)
    if not q_set or not hits:
        return "知识库里没有检索到相关内容，换个说法或补充资料后再试。"

    idf = idf or {}

    def weight(term: str) -> float:
        return idf.get(term, 1.0)

    max_idf = max((weight(t) for t in q_terms), default=1.0) or 1.0

    scored: list[tuple[float, int, str]] = []
    for rank, hit in enumerate(hits, 1):
        rank_prior = 1.0 / (1 + 0.35 * (rank - 1))
        for sent in _candidates(hit["content"]):
            if sent.endswith(_BAD_TAIL):
                continue
            if code_ratio(sent) > 0.06 or _looks_code(sent):   # 代码行不当答案
                continue
            s_terms = set(terms(sent))
            if not s_terms:
                continue
            matched = q_set & s_terms
            if not matched:
                continue
            # 把问题原句本身（文档里的示例代码常把问题抄一遍）剔掉
            if len(sent) < 110 and len(matched) / len(q_set) > 0.7:
                continue
            # IDF 加权：命中 chunk_size 这种稀有词 >> 命中「默认」这种常用词
            gain = sum(weight(t) for t in matched) / max_idf
            score = rank_prior * gain / (len(sent) ** 0.22)
            if sent[-1] not in "。！？!?":     # 半句（滑窗切出来的）降权
                score *= 0.85
            scored.append((score, rank, sent))

    if not scored:
        head = _candidates(hits[0]["content"])[:2]
        body = " ".join(head) or hits[0]["content"][:200]
        return f"（未逐句匹配，以下是最相关片段）\n{body} [1]"

    scored.sort(key=lambda x: -x[0])
    picked, seen = [], set()
    for _score, rank, sent in scored:
        key = sent[:24]
        if key in seen:
            continue
        seen.add(key)
        picked.append((sent.rstrip("。；;") + f"。 [{rank}]", rank))
        if len(picked) >= max_sentences:
            break

    order = sorted(picked, key=lambda x: x[1])
    return "\n".join(f"· {sent}" for sent, _ in order)
