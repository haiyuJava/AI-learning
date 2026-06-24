from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .conversation_log import append_log


DATA_DIR = Path("data")
WIKI_DIR = DATA_DIR / "personal-psychology-wiki"
CHANGELOG_DIR = WIKI_DIR / "changelog"


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(DATA_DIR), *args], text=True, encoding="utf-8", errors="replace", capture_output=True, check=check)


def status() -> str:
    return run_git(["status", "--short"], check=False).stdout.strip()


def write_changelog(message: str, details: str = "") -> Path:
    CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = CHANGELOG_DIR / f"{stamp}.md"
    body = [
        f"# 知识库更新 {stamp}",
        "",
        "## 修改说明",
        message,
        "",
        "## 备注",
        details or "无",
        "",
        "## 回滚",
        "使用 `python -m personal_psych_assistant.ops.kb_versions rollback <commit>` 回滚到指定版本。",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def commit(message: str, details: str = "") -> str:
    changelog = write_changelog(message, details)
    run_git(["add", "personal-psychology-wiki"], check=True)
    completed = run_git(["commit", "-m", f"kb: {message}"], check=False)
    append_log("system", f"Knowledge base version attempt: {message}\nChangelog: {changelog}\n{completed.stdout}\n{completed.stderr}", "kb-version")
    return completed.stdout + completed.stderr


def list_versions(limit: int = 10) -> str:
    return run_git(["log", f"-{limit}", "--oneline", "--", "personal-psychology-wiki"], check=False).stdout.strip()


def diff(commit_ref: str) -> str:
    return run_git(["diff", commit_ref, "--", "personal-psychology-wiki"], check=False).stdout


def rollback(commit_ref: str) -> str:
    run_git(["checkout", commit_ref, "--", "personal-psychology-wiki"], check=True)
    return f"Rolled back personal-psychology-wiki to {commit_ref}. Review and commit if correct."


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Knowledge base version helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_commit = sub.add_parser("commit")
    p_commit.add_argument("message")
    p_commit.add_argument("--details", default="")
    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=10)
    p_diff = sub.add_parser("diff")
    p_diff.add_argument("commit")
    p_rollback = sub.add_parser("rollback")
    p_rollback.add_argument("commit")
    args = parser.parse_args()
    if args.cmd == "status":
        print(status())
    elif args.cmd == "commit":
        print(commit(args.message, args.details))
    elif args.cmd == "list":
        print(list_versions(args.limit))
    elif args.cmd == "diff":
        print(diff(args.commit))
    elif args.cmd == "rollback":
        print(rollback(args.commit))


if __name__ == "__main__":
    main()
