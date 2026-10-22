# -*- coding: utf-8 -*-
"""RAG 主流程：检索 → 增强 → 生成（课件 P80-P83 RetrievalQA 的等价实现）。"""
from __future__ import annotations

import re

from .config import TOP_K, llm_config
from .embedder import code_ratio
from .generator import build_prompt, call_llm, extractive_answer
from .retriever import Retriever
from .store import VectorStore

NO_ANSWER = "根据现有资料无法回答这个问题。可以换个说法，或往 data/ 里补充资料后重建索引。"
_CJK = re.compile(r"[\u4e00-\u9fff]")
# 只由标点/引用编号/空白组成，或极短且无信息量，都判为无效答案
_JUNK = re.compile(r"^[\s\d\[\]（）()。，,、：:；;！!？?\-—+*/\\|]+$")


def _sanitize(answer: str, note: str, hits: list[dict], question: str = "") -> tuple[str, str]:
    """清理小模型的坏输出：过短、只有编号、复读标点。"""
    text = (answer or "").strip()
    if not text:
        return NO_ANSWER, note
    body = _JUNK.sub("", text)
    cjk = len(_CJK.findall(body))
    if _JUNK.match(text) or (cjk < 4 and len(body) < 12):
        return NO_ANSWER, (note or "模型没有给出有效内容，已按“无法回答”处理。")

    # 答案是一段代码（小模型偶尔直接吐代码块）→ 不是用户要的答案
    if code_ratio(text) > 0.45 or text.lstrip().startswith(("from ", "import ", "def ", "class ")):
        return NO_ANSWER, (note or "模型返回了一段代码，不是问题的答案。")

    # 只有把问题原样复读（可能带个 [1]），没有任何信息量 → 也当没答上来
    if question:
        def strip_cites(x: str) -> str:
            return re.sub(r"\[\d+\]|\s+|[？?。，,、：:]", "", x)
        if strip_cites(text) == strip_cites(question) or (
            strip_cites(text).startswith(strip_cites(question))
            and len(strip_cites(text)) - len(strip_cites(question)) < 8
        ):
            return NO_ANSWER, (note or "模型只是复读了问题，没有给出内容。")
    return text, note


class RAGKB:
    def __init__(self, store_dir=None):
        self.store = VectorStore(store_dir)
        self.retriever = Retriever(self.store)
        self._llm_error: str | None = None   # 记住失败原因，避免每次都等超时

    # ———————————————— 只检索 ————————————————
    def retrieve(self, question: str, top_k: int = TOP_K, source_filter: str | None = None):
        return self.retriever.search(question, top_k=top_k, source_filter=source_filter)

    # ———————————————— 检索 + 生成 ————————————————
    def ask(self, question: str, top_k: int = TOP_K, use_llm: bool = True,
            source_filter: str | None = None) -> dict:
        question = (question or "").strip()
        if not question:
            return {"question": "", "answer": "请输入问题。", "mode": "empty", "sources": []}

        hits = self.retriever.search(question, top_k=top_k, source_filter=source_filter)
        if not hits:
            return {
                "question": question,
                "answer": "知识库里没有检索到相关内容。可以换个说法，或往 data/ 里补充资料后重建索引。",
                "mode": "no_hit",
                "sources": [],
            }

        sources = [
            {
                "index": i,
                "source": h["metadata"].get("source", "?"),
                "page": h["metadata"].get("page"),
                "row": h["metadata"].get("row"),
                "sheet": h["metadata"].get("sheet"),
                "score": h["score"],
                "snippet": h["content"][:200].replace("\n", " "),
                "content": h["content"],
            }
            for i, h in enumerate(hits, 1)
        ]

        mode, note, answer = "extractive", "", None

        if use_llm and llm_config() and self._llm_error is None:
            try:
                answer = call_llm(build_prompt(question, hits))
                mode = "llm"
            except Exception as exc:                 # 断网 / 无额度 / 鉴权失败
                self._llm_error = f"{type(exc).__name__}: {exc}"
                note = f"大模型调用失败（{self._llm_error}），已回退为离线抽取式回答。"

        if answer is None:
            answer = extractive_answer(question, hits, idf=self.retriever.idf)
            if not note and use_llm and llm_config() is None:
                note = "未配置大模型（.env 里没有可用 Key），当前为离线抽取式回答。"

        # 小模型偶尔会吐出 "正[1]" 这种半截垃圾，或对库外问题硬编一个答案。
        # 这里做一道保底：答案太短 / 没有任何实质汉字内容 → 当作没答上来。
        answer, note = _sanitize(answer, note, hits, question)

        return {
            "question": question,
            "answer": answer,
            "mode": mode,
            "note": note,
            "sources": sources,
            "prompt": build_prompt(question, hits),
        }

    # ———————————————— 重建索引后热加载 ————————————————
    def reload(self) -> None:
        self.store = VectorStore(self.store.dir)
        self.retriever = Retriever(self.store)
        self._llm_error = None
