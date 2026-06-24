from __future__ import annotations

import html
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


@dataclass
class SourceDocument:
    title: str
    path: str
    kind: str
    text: str


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "br", "section", "div", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "section", "div", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return clean_text(" ".join(self.parts))


def read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return repair_mojibake(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    return repair_mojibake(raw.decode("utf-8", errors="ignore"))


def repair_mojibake(text: str) -> str:
    # Several exported notes are UTF-8 text that was decoded as Latin-1/CP1252
    # before being saved. This round-trip recovers the original Chinese.
    markers = ("æ", "è", "å", "ç", "ä", "â", "ï¼", "ã€")
    if sum(text.count(marker) for marker in markers) < 3:
        return text
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = text.encode(encoding, errors="ignore").decode("utf-8")
        except UnicodeDecodeError:
            continue
        if count_cjk(repaired) > count_cjk(text):
            return repaired
    return text


def count_cjk(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def clean_text(text: str) -> str:
    text = html.unescape(repair_mojibake(text))
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_html(path: Path) -> str:
    parser = _TextHTMLParser()
    parser.feed(read_text_file(path))
    text = parser.text()
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and not line.strip().startswith(("var ", "window.", "document.", "function "))
    ]
    return clean_text("\n".join(lines))


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        runs = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        if runs:
            paragraphs.append("".join(runs))
    return clean_text("\n".join(paragraphs))


def iter_source_documents(notes_dir: Path) -> Iterable[SourceDocument]:
    for path in sorted(notes_dir.rglob("*")):
        if not path.is_file() or "assets" in path.parts:
            continue
        if path.suffix.lower() == ".txt":
            text = read_text_file(path)
            kind = "text"
        elif path.suffix.lower() == ".docx":
            text = extract_docx(path)
            kind = "docx"
        elif path.name.lower() == "index.html":
            text = extract_html(path)
            kind = "html"
        else:
            continue
        if text:
            title = repair_mojibake(path.parent.name if path.name.lower() == "index.html" else path.stem)
            yield SourceDocument(title=title, path=str(path), kind=kind, text=text)


def load_sources(notes_dir: Path) -> list[SourceDocument]:
    return list(iter_source_documents(notes_dir))


def save_sources_json(sources: list[SourceDocument], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(source) for source in sources], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

