from __future__ import annotations

import re


STOP_CHARS = set("的一是在不了和就都而及与或也很更把被这那你我他她它们一个一些自己现在因为所以如果但是")


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if len(part.strip()) >= 8]


def cjk_chars(text: str) -> list[str]:
    return [char for char in text if "\u4e00" <= char <= "\u9fff" and char not in STOP_CHARS]


def terms(text: str) -> set[str]:
    chars = cjk_chars(text)
    grams: set[str] = set(chars)
    grams.update("".join(chars[index : index + 2]) for index in range(max(0, len(chars) - 1)))
    grams.update("".join(chars[index : index + 3]) for index in range(max(0, len(chars) - 2)))
    grams.update(re.findall(r"[A-Za-z0-9_+-]{2,}", text.lower()))
    return {term for term in grams if term.strip()}


def compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"

