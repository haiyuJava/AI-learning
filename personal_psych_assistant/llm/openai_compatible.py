from __future__ import annotations

import os

from openai import OpenAI

from .base import LLMResult


class OpenAICompatibleProvider:
    def __init__(self, name: str, model: str, api_key_env: str, base_url: str | None = None) -> None:
        self.name = name
        self.model = model
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {api_key_env}")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900) -> LLMResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        return LLMResult(text=text.strip(), provider=self.name, model=self.model)

