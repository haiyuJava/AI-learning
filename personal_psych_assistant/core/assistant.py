from __future__ import annotations

import argparse
import sys

from personal_knowledge.indexer import build_index
from personal_knowledge.synthesizer import source_lookup, summarize

from ..knowledge.compiler import compile_wiki
from .answer import answer
from .intent_router import classify_intent
from .recall import NOTES_DIR, WIKI_DIR, classify_profiles, format_cases, recall


def respond(query: str, use_llm: bool = True) -> str:
    intent = classify_intent(query)
    if intent.name == "source_lookup":
        return source_lookup(query)
    if intent.name in {"knowledge_summary", "general_answer"}:
        return summarize(query, use_llm=use_llm)
    if intent.name == "similar_recall":
        profile_match = classify_profiles(query)[0]
        return format_cases(query, recall(query, 4, profile_match.profile), profile_match)
    return answer(query)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Route a personal assistant query to the right local workflow")
    parser.add_argument("query", nargs="*", help="question or current state")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the local wiki before answering")
    parser.add_argument("--no-llm", action="store_true", help="use local retrieval summary only")
    args = parser.parse_args()

    if args.rebuild:
        compile_wiki(NOTES_DIR, WIKI_DIR)
        build_index()
    query = " ".join(args.query).strip() if args.query else input("请输入问题：").strip()
    print(respond(query, use_llm=not args.no_llm))


if __name__ == "__main__":
    main()
