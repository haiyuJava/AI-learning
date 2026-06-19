from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceRecord:
    source_id: str
    title: str
    path: str
    kind: str
    domain: str
    source_type: str
    author: str
    created_at: str | None
    tags: list[str]


@dataclass
class ChunkRecord:
    chunk_id: str
    source_id: str
    title: str
    path: str
    domain: str
    source_type: str
    position: int
    text: str
    tags: list[str]


@dataclass
class SearchResult:
    chunk: ChunkRecord
    score: float
    matched_terms: list[str]

