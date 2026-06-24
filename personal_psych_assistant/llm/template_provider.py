from __future__ import annotations

from .base import LLMResult


class TemplateProvider:
    name = "template"
    model = "local-template"

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900) -> LLMResult:
        prompt = messages[-1]["content"] if messages else ""
        return LLMResult(text=render_from_prompt(prompt), provider=self.name, model=self.model, fallback_used=True)


def section(prompt: str, title: str) -> str:
    marker = f"{title}："
    if marker not in prompt:
        return ""
    start = prompt.index(marker) + len(marker)
    rest = prompt[start:]
    next_markers = [idx for idx in [rest.find("\n\n识别到"), rest.find("\n\n用户认可"), rest.find("\n\n历史经验"), rest.find("\n\n适合"), rest.find("\n\n现在应"), rest.find("\n\n回答要求")] if idx >= 0]
    end = min(next_markers) if next_markers else len(rest)
    return rest[:end].strip()


def render_from_prompt(prompt: str) -> str:
    query = section(prompt, "用户当前问题")
    profile = section(prompt, "识别到的焦虑类型")
    certainty = section(prompt, "用户认可的确定感")
    cases = section(prompt, "历史经验片段")
    actions = section(prompt, "适合的动作")
    avoid = section(prompt, "现在应避免")
    parts = []
    if query:
        parts.append(f"你现在的问题是：{query}")
    if profile:
        parts.append(f"识别到的类型：{profile}")
    if certainty:
        parts.append(certainty)
    if cases:
        parts.append("你过去可以参考的经验：\n" + trim_lines(cases, 8))
    if actions:
        parts.append("现在先做这些：\n" + trim_lines(actions, 4))
    if avoid:
        parts.append("先避免：\n" + trim_lines(avoid, 3))
    return "\n\n".join(part for part in parts if part).strip()


def trim_lines(text: str, limit: int) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:limit])

