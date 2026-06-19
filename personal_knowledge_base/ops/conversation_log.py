from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


LOG_DIR = Path("data/personal-psychology-wiki/conversation-log")


def append_log(role: str, text: str, kind: str = "note") -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now():%Y-%m}.md"
    entry = "\n".join(
        [
            f"\n## {datetime.now():%Y-%m-%d %H:%M:%S} - {role} - {kind}",
            "",
            text.strip(),
            "",
        ]
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a conversation note to the local knowledge log")
    parser.add_argument("text", nargs="*", help="text to append")
    parser.add_argument("--role", default="system", help="speaker role")
    parser.add_argument("--kind", default="note", help="entry kind")
    args = parser.parse_args()
    text = " ".join(args.text).strip() or input("Log text: ").strip()
    path = append_log(args.role, text, args.kind)
    print(f"Logged to {path}")


if __name__ == "__main__":
    main()

