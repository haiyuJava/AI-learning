from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ..knowledge.compiler import THEMES, compile_wiki


WIKI_DIR = Path("data/personal-psychology-wiki")
NOTES_DIR = Path("data/thinking-notes")

CRISIS_WORDS = ["自杀", "不想活", "结束生命", "伤害自己", "伤害别人", "活不下去"]
ANXIETY_WORDS = ["焦虑", "慌", "害怕", "担心", "崩", "压抑", "难受", "失控", "心慌", "烦"]


def load_knowledge() -> dict:
    path = WIKI_DIR / "knowledge.json"
    if not path.exists():
        return compile_wiki(NOTES_DIR, WIKI_DIR)
    return json.loads(path.read_text(encoding="utf-8"))


def match_themes(text: str, knowledge: dict) -> list[dict]:
    scored: list[tuple[int, dict]] = []
    for theme in knowledge.get("themes", []):
        keywords = THEMES.get(theme["name"], [])
        score = sum(text.count(keyword) for keyword in keywords)
        if score:
            scored.append((score, theme))
    if not scored:
        return knowledge.get("themes", [])[:2]
    return [theme for _, theme in sorted(scored, key=lambda item: item[0], reverse=True)[:3]]


def compact_sentence(text: str, limit: int = 170) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_response(user_text: str, knowledge: dict | None = None, brief: bool = False) -> str:
    knowledge = knowledge or load_knowledge()
    text = user_text.strip()
    if not text:
        return "我在。你可以直接说你现在的状态，不需要组织得很完整。"

    if any(word in text for word in CRISIS_WORDS):
        return (
            "我先认真地陪你停在这里。现在最重要的不是分析，而是确保你身边有人和你一起承接这个时刻。"
            "请立刻联系一个可信任的人，或者拨打当地紧急电话。你也可以把危险物品先放远，走到有人在的地方。"
            "等安全感稍微回来，我们再慢慢分析发生了什么。"
        )

    themes = match_themes(text, knowledge)
    primary = themes[0] if themes else None
    theme_name = primary["name"] if primary else "当前压力"
    evidence = primary.get("evidence", [])[:1] if primary else []
    interventions = primary.get("interventions", [])[:3] if primary else ["先喝水", "站起来走两分钟", "写下一件可控小事"]

    if any(word in text for word in ANXIETY_WORDS):
        opening = "我听到了，你现在不是需要被催着解决人生问题，而是需要先把身心从高压里放下来。"
    elif "提醒" in text or "今天" in text or "早上" in text:
        opening = "今天我们把节奏放稳一点。你不需要靠紧绷来维持安全感，先抓住一件真正能推进的小事。"
    elif "复盘" in text or "睡前" in text:
        opening = "我们温和地收一下今天，不审判自己，只看见事实、消耗和一点点进展。"
    else:
        opening = "我在听。我们先不急着下结论，把这件事放到你的心理地图里看一看。"

    lines = [
        opening,
        f"从你的知识库看，这次更像触发了「{theme_name}」。",
    ]
    if brief:
        action = interventions[0] if interventions else "先喝水，然后站起来走两分钟"
        return "\n".join(
            [
                opening,
                f"这次更像是「{theme_name}」被触发了。",
                "先慢一点。你正在经历焦虑，不等于现实已经失控。",
                f"现在只做一个小动作：{action}。",
                "等身体降下来，我们再处理具体问题。",
            ]
        )

    if evidence:
        lines.append(f"这不是凭空来的，你以前也写到过类似线索：{compact_sentence(evidence[0])}")

    lines.extend(
        [
            "现在先做三步：",
            f"第一，先把呼吸放慢，肩膀松下来，告诉自己：我正在经历焦虑，不等于现实已经失控。",
            f"第二，把脑子里的担心分成事实和推测。事实只写一句，推测先放在旁边。",
            f"第三，做一个很小的动作：{interventions[0]}。",
        ]
    )
    if len(interventions) > 1:
        lines.append(f"如果还有力气，再做：{interventions[1]}。")
    lines.append("你不用马上变得积极。先让这一轮焦虑停下来，我们再处理具体问题。")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Local personal psychology assistant")
    parser.add_argument("text", nargs="*", help="state or question")
    parser.add_argument("--rebuild", action="store_true", help="rebuild local psychology wiki first")
    args = parser.parse_args()

    if args.rebuild:
        compile_wiki(NOTES_DIR, WIKI_DIR)
    user_text = " ".join(args.text) if args.text else input("你现在的状态：")
    print(build_response(user_text))


if __name__ == "__main__":
    main()
