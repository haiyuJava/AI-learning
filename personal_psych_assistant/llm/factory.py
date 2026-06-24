from __future__ import annotations

import json
from pathlib import Path

from .base import LLMProvider, LLMResult
from .template_provider import TemplateProvider


CONFIG_PATH = Path("personal_psych_assistant/llm/config.json")


class ProviderChain:
    def __init__(self, providers: list[LLMProvider]) -> None:
        self.providers = providers

    def generate(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 900) -> LLMResult:
        errors: list[str] = []
        for index, provider in enumerate(self.providers):
            try:
                result = provider.generate(messages, temperature, max_tokens)
                result.fallback_used = index > 0 or result.fallback_used
                return result
            except Exception as exc:  # Provider fallback boundary.
                errors.append(f"{getattr(provider, 'name', provider.__class__.__name__)}: {exc}")
        template = TemplateProvider()
        result = template.generate(messages, temperature, max_tokens)
        result.text = result.text + "\n\n[模型不可用，已使用本地模板兜底。错误：" + " | ".join(errors) + "]"
        return result


def load_config(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        return {
            "primary": "template",
            "fallbacks": [],
            "providers": {"template": {"type": "template"}},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def build_provider_chain(path: Path = CONFIG_PATH) -> ProviderChain:
    config = load_config(path)
    names = [config.get("primary", "template"), *config.get("fallbacks", [])]
    providers: list[LLMProvider] = []
    for name in names:
        spec = config.get("providers", {}).get(name, {})
        provider_type = spec.get("type", name)
        try:
            if provider_type == "template":
                providers.append(TemplateProvider())
            elif provider_type in {"openai", "deepseek", "openai_compatible"}:
                from .openai_compatible import OpenAICompatibleProvider

                providers.append(
                    OpenAICompatibleProvider(
                        name=name,
                        model=spec["model"],
                        api_key_env=spec.get("api_key_env", "OPENAI_API_KEY"),
                        base_url=spec.get("base_url"),
                    )
                )
        except Exception:
            if name == "template":
                providers.append(TemplateProvider())
            continue
    if not providers:
        providers.append(TemplateProvider())
    return ProviderChain(providers)
