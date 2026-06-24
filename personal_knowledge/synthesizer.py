from __future__ import annotations

from collections import OrderedDict

from personal_psych_assistant.llm import build_provider_chain

from .retriever import search
from .schema import SearchResult
from .text import compact


def format_evidence(results: list[SearchResult], max_chars: int = 9000) -> str:
    blocks: list[str] = []
    total = 0
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        block = "\n".join(
            [
                f"[{index}] {chunk.title}",
                f"source_id: {chunk.source_id}",
                f"path: {chunk.path}",
                f"domain: {chunk.domain}; type: {chunk.source_type}; position: {chunk.position}",
                compact(chunk.text, 900),
            ]
        )
        total += len(block)
        if total > max_chars:
            break
        blocks.append(block)
    return "\n\n".join(blocks)


def local_summary(query: str, results: list[SearchResult]) -> str:
    if not results:
        return "[mode=knowledge_summary, provider=local-fallback, model=none]\n\n没有找到足够相关的原始记录。"
    lines = [
        "[mode=knowledge_summary, provider=local-fallback, model=none]",
        "",
        "本地检索已找到相关原始片段。当前没有调用大模型，所以这里只给出片段归纳和来源，完整综合需要可用的 LLM provider。",
        "",
        "相关线索：",
    ]
    seen: set[str] = set()
    count = 0
    for result in results:
        text = compact(result.chunk.text, 260)
        if text in seen:
            continue
        seen.add(text)
        count += 1
        lines.append(f"{count}. {text}")
        if count >= 8:
            break
    lines.extend(["", "依据来源："])
    for source in unique_sources(results)[:6]:
        lines.append(f"- {source['title']}：{source['path']}")
    return "\n".join(lines)


def source_lookup(query: str, limit: int = 8) -> str:
    results = search(query, limit=limit)
    if not results:
        return "[mode=source_lookup]\n\n没有找到相关原文。"
    lines = ["[mode=source_lookup]", "", "最相关原文："]
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        lines.extend(
            [
                "",
                f"{index}. {chunk.title}",
                f"   路径：{chunk.path}",
                f"   领域：{chunk.domain}；类型：{chunk.source_type}；位置：chunk {chunk.position}",
                f"   匹配：{', '.join(result.matched_terms[:8]) or '整体相关'}",
                f"   片段：{compact(chunk.text, 220)}",
            ]
        )
    return "\n".join(lines)


def unique_sources(results: list[SearchResult]) -> list[dict[str, str]]:
    sources: OrderedDict[str, dict[str, str]] = OrderedDict()
    for result in results:
        chunk = result.chunk
        if chunk.source_id not in sources:
            sources[chunk.source_id] = {"title": chunk.title, "path": chunk.path}
    return list(sources.values())


def build_summary_prompt(query: str, results: list[SearchResult]) -> str:
    return "\n\n".join(
        [
            "你是私人知识库分析助手。请只基于给定原始片段回答。",
            "你需要综合、归纳、去重，提炼用户过去记录中的观点、原则、经验、教训和可执行策略。",
            "必须区分：用户自己的观点、外部文章观点、你的推断。不要编造未出现在片段中的事实。",
            "每个关键结论后尽量标注来源编号，例如 [1][3]。",
            "输出结构：总体结论、主要观点、可执行策略、风险与不确定性、依据来源。",
            f"用户问题：{query}",
            "原始片段：",
            format_evidence(results),
        ]
    )


def summarize(query: str, use_llm: bool = True, limit: int = 10) -> str:
    results = search(query, limit=limit)
    if not use_llm:
        return local_summary(query, results)
    try:
        result = build_provider_chain().generate(
            [{"role": "user", "content": build_summary_prompt(query, results)}],
            temperature=0.2,
            max_tokens=1400,
        )
    except Exception as exc:
        fallback = local_summary(query, results)
        return fallback + f"\n\n[llm_error={exc}]"
    if result.provider == "template" or not result.text.strip():
        return local_summary(query, results)
    return f"[mode=knowledge_summary, provider={result.provider}, model={result.model}]\n\n{result.text.strip()}"
