from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from personal_knowledge_base.knowledge.ingest import (
    SourceDocument,
    extract_docx,
    extract_html,
    read_text_file,
)

from .schema import ChunkRecord, SourceRecord
from .text import split_sentences


DATA_DIR = Path("data")
INDEX_DIR = DATA_DIR / "knowledge-index"
SOURCES_PATH = INDEX_DIR / "sources.json"
CHUNKS_PATH = INDEX_DIR / "chunks.json"

SKIP_PARTS = {
    "assets",
    "personal-psychology-wiki",
    "knowledge-index",
    "__pycache__",
}

DOMAIN_KEYWORDS = {
    "investment": ["投资", "股票", "基金", "港股", "腾讯", "估值", "收益", "价值"],
    "career": ["工作", "失业", "职业", "面试", "裁员", "上班", "自由职业"],
    "psychology": ["焦虑", "情绪", "安全感", "压抑", "痛苦", "关系"],
    "tech": ["AI", "Python", "RAG", "代码", "技术", "模型"],
}


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def infer_domain(title: str, text: str, path: str) -> str:
    haystack = f"{title}\n{path}\n{text[:3000]}"
    scores = {
        domain: sum(haystack.count(keyword) for keyword in keywords)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    domain, score = max(scores.items(), key=lambda item: item[1])
    return domain if score > 0 else "life"


def infer_source_type(path: Path) -> str:
    path_text = str(path)
    if "thinking-notes" in path_text:
        return "original"
    if path.suffix.lower() in {".md", ".txt", ".docx"}:
        return "reflection"
    return "external"


def infer_created_at(title: str, path: Path) -> str | None:
    match = re.search(r"(20\d{2})[-_年.](\d{1,2})[-_月.](\d{1,2})", title + " " + str(path))
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def title_for(path: Path) -> str:
    return path.parent.name if path.name.lower() == "index.html" else path.stem


def iter_documents(root: Path = DATA_DIR) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        suffix = path.suffix.lower()
        if suffix == ".txt" or suffix == ".md":
            text = read_text_file(path)
            kind = suffix.lstrip(".")
        elif suffix == ".docx":
            text = extract_docx(path)
            kind = "docx"
        elif path.name.lower() == "index.html" or suffix == ".html":
            text = extract_html(path)
            kind = "html"
        else:
            continue
        if text.strip():
            documents.append(SourceDocument(title=title_for(path), path=str(path), kind=kind, text=text))
    return documents


def chunk_text(text: str, max_chars: int = 900, overlap_sentences: int = 1) -> list[str]:
    sentences = split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        if current and current_len + len(sentence) > max_chars:
            chunks.append("\n".join(current).strip())
            current = current[-overlap_sentences:] if overlap_sentences else []
            current_len = sum(len(item) for item in current)
        current.append(sentence)
        current_len += len(sentence)
    if current:
        chunks.append("\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def build_index(data_dir: Path = DATA_DIR, index_dir: Path = INDEX_DIR) -> dict:
    documents = iter_documents(data_dir)
    sources: list[SourceRecord] = []
    chunks: list[ChunkRecord] = []
    seen_text: set[str] = set()

    for document in documents:
        fingerprint = re.sub(r"\s+", "", document.text)[:800]
        if fingerprint in seen_text:
            continue
        seen_text.add(fingerprint)

        path = Path(document.path)
        source_id = stable_id(document.path)
        domain = infer_domain(document.title, document.text, document.path)
        source_type = infer_source_type(path)
        tags = sorted({domain, source_type})
        sources.append(
            SourceRecord(
                source_id=source_id,
                title=document.title,
                path=document.path,
                kind=document.kind,
                domain=domain,
                source_type=source_type,
                author="self" if source_type in {"original", "reflection"} else "external",
                created_at=infer_created_at(document.title, path),
                tags=tags,
            )
        )
        for position, chunk in enumerate(chunk_text(document.text), start=1):
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{source_id}:{position}",
                    source_id=source_id,
                    title=document.title,
                    path=document.path,
                    domain=domain,
                    source_type=source_type,
                    position=position,
                    text=chunk,
                    tags=tags,
                )
            )

    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "sources.json").write_text(
        json.dumps([asdict(source) for source in sources], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (index_dir / "chunks.json").write_text(
        json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (index_dir / "README.md").write_text(
        "\n".join(
            [
                "# 通用个人知识索引",
                "",
                f"- sources: {len(sources)}",
                f"- chunks: {len(chunks)}",
                "- v1 使用本地 JSON + 词法检索；后续可追加 embedding/rerank。",
            ]
        ),
        encoding="utf-8",
    )
    return {"source_count": len(sources), "chunk_count": len(chunks), "index_dir": str(index_dir)}


def ensure_index() -> None:
    if not SOURCES_PATH.exists() or not CHUNKS_PATH.exists():
        build_index()


def main() -> None:
    result = build_index()
    print(f"Generated {result['index_dir']} with {result['source_count']} sources and {result['chunk_count']} chunks")


if __name__ == "__main__":
    main()
