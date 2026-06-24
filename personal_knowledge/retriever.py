from __future__ import annotations

import json
from dataclasses import asdict

from .indexer import CHUNKS_PATH, SOURCES_PATH, ensure_index
from .schema import ChunkRecord, SearchResult, SourceRecord
from .text import terms


def load_sources() -> list[SourceRecord]:
    ensure_index()
    rows = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    return [SourceRecord(**row) for row in rows]


def load_chunks() -> list[ChunkRecord]:
    ensure_index()
    rows = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    return [ChunkRecord(**row) for row in rows]


def search(
    query: str,
    limit: int = 8,
    domain: str | None = None,
    source_type: str | None = None,
    ) -> list[SearchResult]:
    query_terms = terms(query)
    results: list[SearchResult] = []
    for chunk in load_chunks():
        # domain 不为空，且 chunk.domain 与输入的domain不匹配，直接跳过
        if domain and chunk.domain != domain:
            continue
        if source_type and chunk.source_type != source_type:
            continue
        #把当前文本块的“标题 + 正文”揉在一起提取特征词。
        chunk_terms = terms(chunk.title + "\n" + chunk.text)
        #这是 Python 中 set 的交集操作。
        overlap = query_terms & chunk_terms
        if not overlap:
            continue
        title_overlap = query_terms & terms(chunk.title)
        tag_overlap = query_terms & terms(" ".join(chunk.tags))
        # 如果能走到这一步，说明这个文本块和搜索词有交集。接下来就是给它算分（score）：
        # 基础分：只要正文或标题里中一个词，就得 1 分
        score = len(overlap) + len(title_overlap) * 4 + len(tag_overlap) * 3
        # 额外加分项 1：如果中的词在【标题】里，含金量更高，每个词额外 ➕ 4 分！
        matched_terms = sorted([term for term in overlap if len(term) >= 2], key=lambda item: (-len(item), item))[:12]
        results.append(SearchResult(chunk=chunk, score=score, matched_terms=matched_terms))
    return sorted(results, key=lambda item: item.score, reverse=True)[:limit]


def results_as_dicts(results: list[SearchResult]) -> list[dict]:
    rows = []
    for result in results:
        row = asdict(result.chunk)
        row["score"] = result.score
        row["matched_terms"] = result.matched_terms
        rows.append(row)
    return rows
