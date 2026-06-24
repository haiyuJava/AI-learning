from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ops.conversation_log import append_log
from ..llm import build_provider_chain
from .recall import RecallCase, classify_profiles, recall


PROMPT_PATH = Path("personal_psych_assistant/prompts/answer.md")


def render_cases(cases: list[RecallCase]) -> str:
    blocks: list[str] = []
    for index, case in enumerate(cases, start=1):
        block = [
            f"{index}. {case.source.title}",
            f"来源：{case.source.path}",
        ]
        if case.state:
            block.append("当时状态：" + "；".join(case.state[:2]))
        if case.actions:
            block.append("有效动作：" + "；".join(case.actions[:2]))
        if case.certainty:
            block.append("确定感：" + "；".join(case.certainty[:2]))
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def build_prompt(query: str, limit: int = 4) -> tuple[str, str, list[RecallCase]]:
    profile_match = classify_profiles(query)[0]
    cases = recall(query, limit=limit, profile=profile_match.profile)
    profile = profile_match.profile
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(
        query=query,
        profile_name=profile.get("name", profile.get("id", "")),
        certainty=profile.get("certainty", ""),
        cases=render_cases(cases),
        actions="\n".join(f"- {item}" for item in profile.get("actions", [])),
        avoid="\n".join(f"- {item}" for item in profile.get("avoid", [])),
    )
    return prompt, profile.get("id", ""), cases


def answer(query: str, limit: int = 4) -> str:
    prompt, profile_id, _ = build_prompt(query, limit)
    provider = build_provider_chain()
    result = provider.generate([{"role": "user", "content": prompt}])
    append_log("user", query, "query")
    append_log("assistant", f"[provider={result.provider}, model={result.model}, profile={profile_id}]\n\n{result.text}", "answer")
    return result.text


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Generate a final answer using recall + LLM provider fallback")
    parser.add_argument("query", nargs="*", help="question or anxious state")
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    query = " ".join(args.query).strip() if args.query else input("请输入问题：").strip()
    print(answer(query, args.limit))


if __name__ == "__main__":
    main()
