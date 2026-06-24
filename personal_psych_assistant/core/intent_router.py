from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    name: str
    confidence: float
    reason: str


SUMMARY_CONTEXT_WORDS = ["之前", "过去", "记录", "文章", "日志", "知识库", "以前"]
SUMMARY_TASK_WORDS = ["观点", "看法", "总结", "列出来", "有哪些", "归纳", "提炼", "结论", "分析"]
RECALL_WORDS = ["类似", "相似", "当时", "以前怎么", "之前怎么", "怎么处理", "做过什么"]
FACT_WORDS = ["哪篇", "哪里", "什么时候", "有没有写过", "提到过", "原文", "出处"]
CURRENT_STATE_WORDS = ["我现在", "现在", "此刻", "突然", "今天"]
ANXIETY_WORDS = ["焦虑", "慌", "害怕", "担心", "崩", "压抑", "难受", "失控", "心慌", "烦", "痛苦"]


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def classify_intent(query: str) -> Intent:
    text = query.strip()
    if not text:
        return Intent("general_answer", 0.1, "empty query")

    if has_any(text, SUMMARY_CONTEXT_WORDS) and has_any(text, SUMMARY_TASK_WORDS):
        return Intent("knowledge_summary", 0.95, "history context + summary task words")

    if has_any(text, FACT_WORDS):
        return Intent("source_lookup", 0.85, "fact/source lookup words")

    if has_any(text, RECALL_WORDS):
        return Intent("similar_recall", 0.8, "similar past experience words")

    if has_any(text, CURRENT_STATE_WORDS) and has_any(text, ANXIETY_WORDS):
        return Intent("emotional_support", 0.9, "current state + anxiety words")

    if has_any(text, ANXIETY_WORDS):
        return Intent("emotional_support", 0.75, "anxiety words")

    if has_any(text, SUMMARY_TASK_WORDS):
        return Intent("knowledge_summary", 0.65, "summary task words")

    return Intent("general_answer", 0.4, "fallback")
