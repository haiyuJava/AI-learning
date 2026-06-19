from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .ingest import SourceDocument, load_sources, save_sources_json
from .profiles import ensure_default_profiles, load_profiles


THEMES: dict[str, list[str]] = {
    "安全感与稳定": ["安全", "安定", "稳定", "底气", "依靠", "不自信", "无助", "漂泊"],
    "工作压力与生存焦虑": ["工作", "裁员", "大厂", "面试", "失业", "外包", "高薪", "996", "生存"],
    "未来失控与逃离冲动": ["未来", "逃离", "退休", "焦虑", "担心", "不确定", "危机"],
    "身体行动与情绪排解": ["徒步", "运动", "散步", "出汗", "自然", "放空", "身体", "走出去"],
    "连接关系与陪伴": ["朋友", "陪伴", "新人", "群", "连接", "伙伴", "生活"],
    "试错与新生活方式": ["试错", "生活方式", "探索", "好玩", "平常心", "节奏", "自由"],
    "投资与长期主线": ["投资", "股票", "基金", "收益", "决策", "主线", "知行合一"],
    "自责与高压防御": ["自责", "对抗", "紧张", "防御", "压抑", "痛苦", "警戒", "苛求"],
}

INTERVENTIONS: dict[str, list[str]] = {
    "安全感与稳定": ["先把今天缩小到一个可控动作", "提醒自己：不需要靠持续紧张来证明安全", "把钱、住处、工作下一步分别列清"],
    "工作压力与生存焦虑": ["只处理最近 24 小时内能推进的一件事", "把面试/学习拆到 25 分钟", "避免用大厂或高薪重新压榨自己"],
    "未来失控与逃离冲动": ["区分事实、推测和最坏想象", "把未来问题写成今天的一个小实验", "暂停反复推演退休/逃离画面"],
    "身体行动与情绪排解": ["出门走 20 到 40 分钟", "让身体先动起来，再思考复杂问题", "走到能出汗但不过度疲劳即可"],
    "连接关系与陪伴": ["主动联系一个低压力的人", "找一个共同打卡或散步的场景", "不要把所有压力都关在房间里独自消化"],
    "试错与新生活方式": ["允许今天只做小规模试错", "用好玩和可持续替代严肃用力", "每天保留一点探索空间"],
    "投资与长期主线": ["把投资主线当作长期系统，不用今天证明全部", "只做符合规则的一小步", "避免在情绪高压时做重大决策"],
    "自责与高压防御": ["把自责句改写成处境描述", "提醒自己：这是旧防御被触发", "先降压，再决定要不要继续努力"],
}


@dataclass
class ThemeSummary:
    name: str
    score: int
    sources: list[str]
    evidence: list[str]
    interventions: list[str]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", text)
    return [part.strip() for part in parts if len(part.strip()) >= 8]


def build_theme_summaries(sources: list[SourceDocument]) -> list[ThemeSummary]:
    theme_sources: dict[str, set[str]] = defaultdict(set)
    theme_evidence: dict[str, list[str]] = defaultdict(list)
    theme_scores: Counter[str] = Counter()

    for source in sources:
        sentences = split_sentences(source.text)
        for theme, keywords in THEMES.items():
            score = sum(source.text.count(keyword) for keyword in keywords)
            if score:
                theme_scores[theme] += score
                theme_sources[theme].add(source.title)
            for sentence in sentences:
                if len(theme_evidence[theme]) >= 6:
                    break
                if any(keyword in sentence for keyword in keywords):
                    theme_evidence[theme].append(sentence[:180])

    summaries = [
        ThemeSummary(
            name=theme,
            score=theme_scores[theme],
            sources=sorted(theme_sources[theme]),
            evidence=theme_evidence[theme][:6],
            interventions=INTERVENTIONS[theme],
        )
        for theme in THEMES
        if theme_scores[theme] > 0
    ]
    return sorted(summaries, key=lambda item: item.score, reverse=True)


def write_markdown(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def compile_wiki(notes_dir: Path, wiki_dir: Path) -> dict:
    sources = load_sources(notes_dir)
    wiki_dir.mkdir(parents=True, exist_ok=True)
    save_sources_json(sources, wiki_dir / "source_index.json")
    profiles_dir = wiki_dir / "profiles"
    ensure_default_profiles(profiles_dir)

    summaries = build_theme_summaries(sources)
    data = {
        "source_count": len(sources),
        "themes": [asdict(summary) for summary in summaries],
        "profiles": load_profiles(profiles_dir),
    }
    (wiki_dir / "knowledge.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    overview_lines = [
        f"- 原始资料数量：{len(sources)}",
        "- 资料来源：`data/thinking-notes` 下的 txt/docx，以及生活杂谈目录中每篇 `index.html` 的正文。",
        "- HTML 的 `assets` 被忽略，没有作为知识输入。",
        "- 这个 Wiki 是编译层：它提炼主题、证据、反向链接、焦虑 profile 和干预策略，而不是简单切片检索。",
        "- 可编辑 profile 位于 `profiles/*.json`，用于区分工作焦虑、人际关系焦虑等不同召回策略。",
    ]
    write_markdown(wiki_dir / "README.md", "私人心理知识库", "\n".join(overview_lines))

    profile_body = [
        "这个知识库用于把你的随笔编译成可召回、可迭代的心理辅助资料。它先识别焦虑类型，再召回对应 profile、反向链接和历史经验。",
        "",
        "## 主要主题",
    ]
    for summary in summaries:
        profile_body.append(f"- [[{summary.name}]]：出现强度 {summary.score}，关联资料 {len(summary.sources)} 篇")
    write_markdown(wiki_dir / "我的心理画像.md", "我的心理画像", "\n".join(profile_body))

    for summary in summaries:
        body = [
            "## 反向链接",
            "- [[我的心理画像]]",
            "- [[焦虑急救流程]]",
            "",
            "## 关联来源",
            *[f"- {source}" for source in summary.sources[:12]],
            "",
            "## 证据片段",
            *[f"- {evidence}" for evidence in summary.evidence],
            "",
            "## 适合的干预",
            *[f"- {item}" for item in summary.interventions],
        ]
        write_markdown(wiki_dir / f"{summary.name}.md", summary.name, "\n".join(body))

    profiles_index = ["## 焦虑类型 Profile", ""]
    for profile in load_profiles(profiles_dir):
        profile_name = profile["name"]
        linked_themes = profile.get("linked_themes", [])
        preferred_sources = profile.get("preferred_sources", [])
        profiles_index.extend(
            [
                f"### [[{profile_name}]]",
                f"- 配置文件：`profiles/{profile['id']}.json`",
                f"- 关联主题：{', '.join(f'[[{theme}]]' for theme in linked_themes)}",
                f"- 优先来源：{', '.join(preferred_sources[:5])}",
                "",
            ]
        )
        profile_body = [
            "## 反向链接",
            "- [[我的心理画像]]",
            "- [[焦虑类型索引]]",
            *[f"- [[{theme}]]" for theme in linked_themes],
            "",
            "## 触发词",
            ", ".join(profile.get("triggers", [])),
            "",
            "## 确定感模板",
            profile.get("certainty", ""),
            "",
            "## 适合的动作",
            *[f"- {item}" for item in profile.get("actions", [])],
            "",
            "## 不适合的回应",
            *[f"- {item}" for item in profile.get("avoid", [])],
            "",
            "## 优先召回来源",
            *[f"- {item}" for item in preferred_sources],
        ]
        write_markdown(wiki_dir / f"{profile_name}.md", profile_name, "\n".join(profile_body))
    write_markdown(wiki_dir / "焦虑类型索引.md", "焦虑类型索引", "\n".join(profiles_index))

    emergency_body = "\n".join(
        [
            "当你说“我现在很焦虑”时，助手按这个顺序工作：",
            "",
            "1. 先承认身体和情绪正在高压中，不急着讲大道理。",
            "2. 识别这次更像哪个主题：安全感、工作压力、未来失控、关系陪伴、自责防御。",
            "3. 区分事实、推测和灾难化想象。",
            "4. 给一个低成本动作：喝水、站起来、走路、写下一件可控事、联系一个人。",
            "5. 如果出现自伤或伤害他人的表达，立即建议联系身边可信的人和当地紧急服务。",
        ]
    )
    write_markdown(wiki_dir / "焦虑急救流程.md", "焦虑急救流程", emergency_body)

    return data


def main() -> None:
    compile_wiki(Path("data/thinking-notes"), Path("data/personal-psychology-wiki"))
    print("Generated data/personal-psychology-wiki")


if __name__ == "__main__":
    main()
