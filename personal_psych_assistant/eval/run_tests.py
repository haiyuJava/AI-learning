from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core.answer import answer
from ..core.assistant import respond
from ..core.intent_router import classify_intent
from ..core.recall import classify_profiles, format_cases, recall


FIXTURE_PATH = Path(__file__).with_name("fixtures") / "recall_cases.json"
INTENT_FIXTURE_PATH = Path(__file__).with_name("fixtures") / "intent_cases.json"


def run(use_llm: bool = False) -> int:
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    intent_cases = json.loads(INTENT_FIXTURE_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in cases:
        query = case["input"]
        profile_match = classify_profiles(query)[0]
        profile_id = profile_match.profile.get("id")
        if profile_id != case.get("expected_profile"):
            failures.append(f"{query}: expected profile {case.get('expected_profile')}, got {profile_id}")
        output = answer(query, limit=4) if use_llm else format_cases(query, recall(query, 4, profile_match.profile), profile_match)
        for expected in case.get("must_include", []):
            if expected not in output:
                failures.append(f"{query}: missing `{expected}`")
    for case in intent_cases:
        query = case["input"]
        intent = classify_intent(query)
        if intent.name != case["expected_intent"]:
            failures.append(f"{query}: expected intent {case['expected_intent']}, got {intent.name}")
        if case["expected_intent"] in {"knowledge_summary", "source_lookup"}:
            output = respond(query, use_llm=False)
            for expected in case.get("must_include", []):
                if expected not in output:
                    failures.append(f"{query}: routed output missing `{expected}`")
            for unexpected in case.get("must_not_include", []):
                if unexpected in output:
                    failures.append(f"{query}: routed output should not include `{unexpected}`")
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Run personal psychology assistant regression tests")
    parser.add_argument("--llm", action="store_true", help="test final answer provider instead of local recall format")
    args = parser.parse_args()
    raise SystemExit(run(args.llm))


if __name__ == "__main__":
    main()
