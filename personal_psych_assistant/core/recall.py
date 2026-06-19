from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..knowledge.compiler import compile_wiki
from ..knowledge.profiles import load_profiles


WIKI_DIR = Path("data/personal-psychology-wiki")
NOTES_DIR = Path("data/thinking-notes")
SOURCE_INDEX = WIKI_DIR / "source_index.json"
PROFILES_DIR = WIKI_DIR / "profiles"
FEEDBACK_DIR = WIKI_DIR / "feedback"

ANXIETY_WORDS = [
    "焦虑",
    "担心",
    "害怕",
    "心慌",
    "压抑",
    "难受",
    "无力",
    "失控",
    "紧张",
    "痛苦",
    "危机",
    "不自信",
    "无助",
]

ACTION_WORDS = [
    "出去",
    "徒步",
    "散步",
    "运动",
    "朋友",
    "吃饭",
    "联系",
    "写",
    "复盘",
    "调整",
    "尝试",
    "试错",
    "放松",
    "放空",
    "走",
    "学",
    "做",
]

RESULT_WORDS = [
    "缓解",
    "有效",
    "开心",
    "舒服",
    "放松",
    "底气",
    "动力",
    "安全感",
    "确定",
    "意识到",
    "明白",
    "可以",
    "应该",
    "需要",
    "不用",
    "没必要",
]

STOP_CHARS = set("的一是在不了和就都而及与或也很更把被这那你我他她它们一个一些自己现在因为所以如果但是")


@dataclass
class Source:
    title: str
    path: str
    kind: str
    text: str


@dataclass
class RecallCase:
    source: Source
    score: float
    similar_terms: list[str]
    state: list[str]
    actions: list[str]
    certainty: list[str]


@dataclass
class ProfileMatch:
    profile: dict[str, Any]
    score: float
    matched_triggers: list[str]


def load_sources() -> list[Source]:
    if not SOURCE_INDEX.exists():
        compile_wiki(NOTES_DIR, WIKI_DIR)
    rows = json.loads(SOURCE_INDEX.read_text(encoding="utf-8"))
    sources: list[Source] = []
    seen: set[str] = set()
    seen_titles: set[str] = set()
    for row in rows:
        text = re.sub(r"\s+", "", row["text"])
        fingerprint = text[:600]
        title_key = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", row["title"])
        title_key = re.sub(r"[_\s—-]+", "", title_key)
        if fingerprint in seen or title_key in seen_titles:
            continue
        seen.add(fingerprint)
        seen_titles.add(title_key)
        sources.append(Source(**row))
    for path in sorted(FEEDBACK_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
        fingerprint = re.sub(r"\s+", "", text)[:600]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        sources.append(Source(title=title, path=str(path), kind="feedback", text=text))
    return sources


def classify_profiles(query: str) -> list[ProfileMatch]:
    profiles = load_profiles(PROFILES_DIR)
    query_terms = terms(query)
    matches: list[ProfileMatch] = []
    for profile in profiles:
        triggers = profile.get("triggers", [])
        linked_themes = profile.get("linked_themes", [])
        preferred_sources = profile.get("preferred_sources", [])
        matched_triggers = [trigger for trigger in triggers if trigger in query]
        trigger_score = sum(10 + len(trigger) for trigger in matched_triggers)
        theme_score = sum(len(query_terms & terms(theme)) * 2 for theme in linked_themes)
        source_score = sum(len(query_terms & terms(source)) for source in preferred_sources)
        anxiety_score = 4 if any(word in query for word in ANXIETY_WORDS) else 0
        score = trigger_score + theme_score + source_score + anxiety_score
        if score > 0:
            matches.append(ProfileMatch(profile=profile, score=score, matched_triggers=matched_triggers))
    if not matches:
        general = next((profile for profile in profiles if profile.get("id") == "general"), profiles[0])
        return [ProfileMatch(profile=general, score=1, matched_triggers=[])]
    return sorted(matches, key=lambda item: item.score, reverse=True)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if len(part.strip()) >= 8]


def cjk_chars(text: str) -> list[str]:
    return [char for char in text if "\u4e00" <= char <= "\u9fff" and char not in STOP_CHARS]


def terms(text: str) -> set[str]:
    chars = cjk_chars(text)
    grams: set[str] = set(chars)
    grams.update("".join(chars[index : index + 2]) for index in range(max(0, len(chars) - 1)))
    grams.update("".join(chars[index : index + 3]) for index in range(max(0, len(chars) - 2)))
    grams.update(re.findall(r"[A-Za-z0-9_+-]{2,}", text.lower()))
    return {term for term in grams if term.strip()}


def compact(text: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def sentence_score(sentence: str, query_terms: set[str], words: list[str]) -> float:
    sent_terms = terms(sentence)
    overlap = len(query_terms & sent_terms)
    keyword_score = sum(3 for word in words if word in sentence)
    return overlap + keyword_score


def pick_sentences(sentences: list[str], query_terms: set[str], words: list[str], limit: int) -> list[str]:
    scored = [
        (sentence_score(sentence, query_terms, words), index, sentence)
        for index, sentence in enumerate(sentences)
    ]
    picked = [sentence for score, _, sentence in sorted(scored, reverse=True) if score > 0]
    return [compact(sentence) for sentence in picked[:limit]]


def find_actions_after_state(sentences: list[str], query_terms: set[str], limit: int) -> list[str]:
    state_indexes = [
        index
        for index, sentence in enumerate(sentences)
        if any(word in sentence for word in ANXIETY_WORDS) or len(terms(sentence) & query_terms) >= 3
    ]
    candidates: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        if not any(word in sentence for word in ACTION_WORDS + RESULT_WORDS):
            continue
        distance_bonus = 0.0
        if state_indexes:
            nearest = min(abs(index - state_index) for state_index in state_indexes)
            distance_bonus = max(0, 5 - nearest) * 0.8
        score = sentence_score(sentence, query_terms, ACTION_WORDS + RESULT_WORDS) + distance_bonus
        if score > 0:
            candidates.append((score, index, sentence))
    return [compact(sentence) for score, _, sentence in sorted(candidates, reverse=True)[:limit]]


def source_profile_bonus(source: Source, profile: dict[str, Any]) -> float:
    bonus = 0.0
    title = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", source.title)
    for preferred in profile.get("preferred_sources", []):
        if preferred in title or title in preferred:
            bonus += 45
    source_text = source.title + "\n" + source.text[:2000]
    for theme in profile.get("linked_themes", []):
        bonus += len(terms(theme) & terms(source_text)) * 0.6
    return bonus


def recall(query: str, limit: int = 4, profile: dict[str, Any] | None = None) -> list[RecallCase]:
    query_terms = terms(query)
    sources = load_sources()
    cases: list[RecallCase] = []

    for source in sources:
        source_terms = terms(source.title + "\n" + source.text)
        overlap = query_terms & source_terms
        if not overlap:
            continue
        keyword_boost = sum(8 for word in ANXIETY_WORDS if word in query and word in source.text)
        title_boost = len(query_terms & terms(source.title)) * 2
        profile_boost = source_profile_bonus(source, profile) if profile else 0
        feedback_title_overlap = query_terms & terms(source.title)
        feedback_boost = 80 if source.kind == "feedback" and feedback_title_overlap else 0
        score = len(overlap) + keyword_boost + title_boost + profile_boost + feedback_boost
        sentences = split_sentences(source.text)
        state = pick_sentences(sentences, query_terms, ANXIETY_WORDS, 2)
        actions = find_actions_after_state(sentences, query_terms, 3)
        certainty = pick_sentences(sentences, query_terms, RESULT_WORDS, 2)
        if state or actions or certainty:
            cases.append(
                RecallCase(
                    source=source,
                    score=score,
                    similar_terms=sorted(
                        [term for term in overlap if len(term) >= 2],
                        key=lambda term: (-len(term), term),
                    )[:10],
                    state=state,
                    actions=actions,
                    certainty=certainty,
                )
            )

    return sorted(cases, key=lambda item: item.score, reverse=True)[:limit]


def format_cases(query: str, cases: list[RecallCase], profile_match: ProfileMatch | None = None) -> str:
    if not cases:
        return (
            "这次没有找到足够相似的历史片段。你可以把当前焦虑说得更具体一点："
            "比如是工作、钱、未来、关系、身体状态，还是对自己失去信心。"
        )

    lines = [
        "我先不安慰你，直接把你过去处理过的相似经验找出来。",
        f"当前问题：{query}",
        "",
    ]
    if profile_match:
        profile = profile_match.profile
        lines.extend(
            [
                f"识别到的焦虑类型：{profile.get('name', profile.get('id', '未命名'))}",
                f"匹配触发词：{', '.join(profile_match.matched_triggers) or '整体语义匹配'}",
                "",
                "先把这个类型下你认可的确定感放在最前面：",
                profile.get("certainty", ""),
                "",
            ]
        )
    lines.append(f"找到 {len(cases)} 个相似片段：")

    for index, case in enumerate(cases, start=1):
        lines.extend(
            [
                "",
                f"{index}. {case.source.title}",
                f"   相似点：{', '.join(case.similar_terms[:6]) or '整体语义相近'}",
                f"   来源：{case.source.path}",
            ]
        )
        if case.state:
            lines.append("   当时的状态：")
            lines.extend(f"   - {sentence}" for sentence in case.state)
        if case.actions:
            lines.append("   当时你做过/发现有效的事：")
            lines.extend(f"   - {sentence}" for sentence in case.actions)
        if case.certainty:
            lines.append("   可以拿回来的确定感：")
            lines.extend(f"   - {sentence}" for sentence in case.certainty)

    lines.extend(
        [
            "",
        ]
    )
    if profile_match:
        actions = profile_match.profile.get("actions", [])
        if actions:
            lines.append("这个类型下，当前最适合的动作：")
            lines.extend(f"- {action}" for action in actions[:3])
        avoid = profile_match.profile.get("avoid", [])
        if avoid:
            lines.append("")
            lines.append("现在先避免：")
            lines.extend(f"- {item}" for item in avoid[:2])
    else:
        lines.append("给你一个很短的结论：你之前不是没有办法。你的知识库里反复出现的有效路径是：先离开封闭空间，让身体动起来，降低高压推演，再把问题缩小成今天能做的一步。")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Recall similar past anxiety cases from the local psychology wiki")
    parser.add_argument("query", nargs="*", help="current anxious state or question")
    parser.add_argument("--limit", type=int, default=4, help="number of recalled cases")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the local wiki before recall")
    args = parser.parse_args()

    if args.rebuild:
        compile_wiki(NOTES_DIR, WIKI_DIR)
    query = " ".join(args.query).strip() if args.query else input("你现在焦虑的具体内容：").strip()
    profile_match = classify_profiles(query)[0]
    print(format_cases(query, recall(query, args.limit, profile_match.profile), profile_match))


if __name__ == "__main__":
    main()
