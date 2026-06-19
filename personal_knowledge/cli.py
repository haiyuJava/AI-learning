from __future__ import annotations

import argparse
import sys

from .indexer import build_index
from .synthesizer import source_lookup, summarize


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Personal knowledge system")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("index", help="build general knowledge index")

    source_parser = subparsers.add_parser("source", help="find original sources")
    source_parser.add_argument("query", nargs="*")
    source_parser.add_argument("--rebuild", action="store_true")
    source_parser.add_argument("--limit", type=int, default=8)

    summary_parser = subparsers.add_parser("summarize", help="summarize retrieved knowledge")
    summary_parser.add_argument("query", nargs="*")
    summary_parser.add_argument("--rebuild", action="store_true")
    summary_parser.add_argument("--no-llm", action="store_true")
    summary_parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    if args.command == "index":
        result = build_index()
        print(f"Generated {result['index_dir']} with {result['source_count']} sources and {result['chunk_count']} chunks")
        return
    if getattr(args, "rebuild", False):
        build_index()
    query = " ".join(getattr(args, "query", [])).strip() or input("请输入问题：").strip()
    if args.command == "source":
        print(source_lookup(query, limit=args.limit))
        return
    if args.command == "summarize":
        print(summarize(query, use_llm=not args.no_llm, limit=args.limit))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
