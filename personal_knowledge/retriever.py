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
        if domain and chunk.domain != domain:
            continue
        if source_type and chunk.source_type != source_type:
            continue
        chunk_terms = terms(chunk.title + "\n" + chunk.text)
        overlap = query_terms & chunk_terms
        if not overlap:
            continue
        title_overlap = query_terms & terms(chunk.title)
        tag_overlap = query_terms & terms(" ".join(chunk.tags))
        score = len(overlap) + len(title_overlap) * 4 + len(tag_overlap) * 3
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
