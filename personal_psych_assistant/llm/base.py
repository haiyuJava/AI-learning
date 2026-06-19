from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    fallback_used: bool = False


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900) -> LLMResult:
        ...

