#!/usr/bin/env python3
"""
Reddit 音乐 Prompt 爬取器 v1.4.0

设计思路：
1. 多源获取：RSS Feed（主力）+ JSON API（CI 环境备用）
2. Prompt 检测：用内容特征识别真正的音乐提示词，过滤掉问答/讨论/求助帖
3. 质量排序：不再依赖不可靠的点赞数，改用 Prompt 质量评分

什么算「真正的音乐 Prompt」：
  ✅ [rock] [bpm:120] [lo-fi] ... 带结构标签的完整提示词
  ✅ 包含技术参数（BPM/调性/乐器）的描述性文本
  ❌ "Help! Why does my song sound bad?" — 求助帖
  ❌ "How do I make X style?" — 问题帖
  ❌ "Check out this cool song I made!" — 分享帖（无实际 prompt 文本）
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.constants import (
    MUSIC_KEYWORDS,
    TECH_KEYWORDS,
    STRUCTURE_TAGS,
    GENRES,
    INSTRUMENTS,
)


# ============================================================
#  数据源策略：RSS 优先，JSON 兜底
# ============================================================

def _fetch_via_rss(subreddit: str, limit: int = 25) -> list:
    """方式一：通过 RSS Feed 获取（无需认证，大部分环境可用）"""
    try:
        import feedparser

        url = config.reddit.RSS_FEED_URL_TEMPLATE.format(subreddit=subreddit)
        feed = feedparser.parse(
            url,
            request_headers={
                "User-Agent": "MUSICprompt-RSS/1.4.0 (by /u/MUSICprompt-team)"
            },
        )

        if feed.bozo or not feed.entries:
            return []

        posts = []
        for entry in feed.entries[:limit]:
            content_raw = entry.get("summary", "") or entry.get("description", "") or ""
            title = _clean_html(entry.get("title", ""))
            content = _clean_html(content_raw)

            if not content or len(content.strip()) < 30:
                continue

            upvotes = _extract_upvotes_from_rss(content_raw)
            posts.append({
                "id": entry.get("id", "").split("/")[-1] or "",
                "title": title,
                "content": content[:2000],
                "upvotes": max(upvotes, 0),
                "author": _extract_author(entry),
                "url": entry.get("link", ""),
                "subreddit": subreddit,
                "source": "rss",
            })

        return posts

    except ImportError:
        return []
    except Exception:
        return []


def _fetch_via_json(subreddit: str, limit: int = 25) -> list:
    """方式二：通过 JSON API 获取（CI/GitHub Actions 环境通常可用）"""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"

    try:
        req = __import__("urllib.request", fromlist=["Request"]).Request(
            url,
            headers={
                "User-Agent": "MUSICprompt-Bot/1.4.0 (by /u/MUSICprompt-team)"
            },
        )
        with __import__("urllib.request", fromlist=["urlopen"]).urlopen(
            req, timeout=config.reddit.REQUEST_TIMEOUT
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        posts = []
        for child in data["data"]["children"]:
            post = child["data"]
            if not post.get("selftext"):
                continue

            posts.append({
                "id": post["id"],
                "title": post["title"],
                "content": post["selftext"][:2000],
                "upvotes": post.get("score", 0),
                "author": post.get("author", "unknown"),
                "url": f"https://reddit.com{post['permalink']}",
                "subreddit": subreddit,
                "source": "json",
            })

        return posts

    except Exception:
        return []


def fetch_reddit_posts(subreddit: str) -> list:
    """
    获取 Reddit 子版块帖子（自动选择最佳数据源）
    策略：先尝试 RSS，如果结果为空则 fallback 到 JSON API
    """
    posts = _fetch_via_rss(subreddit, limit=30)

    if posts:
        print(f"  r/{subreddit}: RSS 获取 {len(posts)} 条")
        return posts

    posts = _fetch_via_json(subreddit, limit=30)

    if posts:
        print(f"  r/{subreddit}: JSON fallback 获取 {len(posts)} 条")
        return posts

    print(f"  r/{subreddit}: 两种方式均未获取到数据")
    return []


# ============================================================
# 核心：Prompt 检测与质量评分
#
# 真实 Suno Prompt 的两种标准格式:
#   A) Style of Music:  "rock pop, 118 BPM, baritone guitar lead, ..."
#      → 逗号分隔, 1-2流派 + 乐器 + 形容词 + 情绪 (≤120字符)
#   B) Lyrics with Meta Tags:
#      [Intro][Ambient pad]
#      [Verse 1]
#      歌词...
#      [Chorus][Full energy]
# ============================================================

JUNK_TITLE_PATTERNS = [
    r"\?",
    r"(?i)\bhelp\b",
    r"(?i)\bwhy\s+(does|do|is|are|did|won't)\b",
    r"(?i)\bhow\s+(do|does|can|i|to)\b",
    r"(?i)\bbug(s)?\b",
    r"(?i)\berror(s)?\b",
    r"(?i)\bissue(s)?\b",
    r"(?i)\bproblem(s)?\b",
    r"(?i)\bsurvey\b",
    r"(?i)\bpoll\b",
    r"(?i)\bmod\s+post\b",
    r"(?i)\bstick(y|ied|ies)?\b",
    r"(?i)\brule(s)?\b",
    r"(?i)\bban(ned|ning)?\b",
    r"(?i)^(\[removed\]|\[deleted\])$",
]

STRUCTURE_META_TAGS = [
    r"\[\s*intro\s*\]",
    r"\[\s*verse\s*\]",
    r"\[\s*chorus\s*\]",
    r"\[\s*bridge\s*\]",
    r"\[\s*outro\s*\]",
    r"\[\s*(?:pre-?)?chorus\s*\]",
    r"\[\s*hook\s*\]",
    r"\[\s*solo\s*\]",
    r"\[\s*build\s*\]",
    r"\[\s*drop\s*\]",
    r"\[\s*break(?:down)?\s*\]",
    r"\[\s*interlude\s*\]",
]

COMPOUND_TAG_PATTERN = r"\[[^\]]{2,25}\](?:\s*\[[^\]]{2,25}\]){1,}"

BPM_PATTERNS = [
    r"\b\d{2,3}\s*BPM\b",
    r"\bBPM\s*[:\-]?\s*\d{2,3}\b",
    r"\b(?:bpm|tempo)\s*[:\-]?\s*\d{2,3}\b",
]

KEY_SIGNATURE_PATTERN = r"\b(?:key|scale)\s*[:\-]?\s*[a-g][#]?\s*(?:major|minor|maj|min)\b"

SHARING_LANGUAGE = [
    r"(?i)(?:my\s+)?prompt\s*[:\-]",
    r"(?i)here'?s?\s+(?:my\s+)?prompt",
    r"(?i)i\s+(?:used|wrote|tried)\s+(?:this\s+)?prompt",
    r"(?i)style\s+of\s+music\s*[:\-]",
    r"(?i)(?:lyrics?|meta\s*tags?)\s*[:\-]",
    r"(?i)try\s+(?:this\s+)?(?:prompt|style)",
    r"(?i)prompt\s+(?:for|that|was|i)",
    r"(?i)(?:got|generated|created)\s+(?:this\s+)?(?:with|using)",
]

STYLE_TAG_DENSE_PATTERN = (
    r"(?:"
    r"(?:acoustic|ambient|EDM|jazz|rock|pop|hip\s*hop|R&B|soul|techno|synth\s*pop|country|reggae|blues|ballad|lo-fi|indie|metal|punk|orchestra|gospel)"
    r"|(?:piano|cello|drums?|synth|guitar|bass|harpsichord|Rhodes|strings?|brass|percussion|saxophone|organ|flute|violin|trumpet)"
    r")\s*,\s*"
    r"(?:"
    r"(?:upbeat|melancholic|energetic|dark|intense|romantic|haunting|joyful|somber|ominous|dramatic|chill|party|nostalgic|cinematic|epic|warm|crisp|raw|polished|groovy|atmospheric)"
    r"|(?:male|female|duet|choir|whisper|falsetto|operatic|baritone|alto|soprano|breathy|husky|soulful)"
    r"|(?:distorted|crunchy|reverb|delay|compression|saturation|analog|digital|clean|muddy)"
    r")"
)

FIRST_PERSON_PATTERNS = [
    r"\bi\s+(?:have|'ve|am|'m|was|think|feel|believe|noticed|found|realized|started|been|just|always|never|really|actually|honestly)",
    r"\bmy\s+(?:song|track|music|prompt|experience|opinion|thought|take|issue|problem|story|project|album)",
    r"\bi'd\s+(?:like|love|prefer|recommend)",
    r"\bin\s+my\s+(?:experience|opinion|humble)",
]

DISCUSSION_WORDS = [
    r"(?i)\bawful\b",
    r"(?i)\bruin(?:ing|ed)?\b",
    r"(?i)\bmagic\s+wand\b",
    r"(?i)\bgeneralize[s]?\b",
    r"(?i)\bdoesn'?t\s+(?:work|matter|make)",
    r"(?i)\bit\s+doesn'?t\s+matter\b",
    r"(?i)boring|annoying|frustrating|terrible|horrible",
    r"(?i)(?:however|although|but)\s+i\b",
]


def is_junk_post(title: str) -> bool:
    for pattern in JUNK_TITLE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False


def is_real_prompt(title: str, content: str) -> Tuple[bool, str]:
    """
    判断帖子是否真正在分享一个音乐生成 Prompt (v2)

    Layer 1 - 正信号检测（必须 >=2 分）:
      结构元标签(3分), 组合标签(3分), BPM(2分), 分享语言(2分), 风格标签串(2分), 调性(1分)

    Layer 2 - 负信号扣分:
      第一人称过密(>=4处:-3, >=2处:-1), 吐槽词(>=2处:-2, >=1处:-1)
      净分 < 1 则拦截

    Layer 3 - 格式门槛: >=5 个逗号
    """
    combined = f"{title} {content}"
    combined_lower = combined.lower()
    content_lower = content.lower()

    positive_score = 0

    for pattern in STRUCTURE_META_TAGS:
        if re.search(pattern, content_lower):
            positive_score += 3
            break

    if re.search(COMPOUND_TAG_PATTERN, content_lower):
        positive_score += 3

    for pattern in BPM_PATTERNS:
        if re.search(pattern, combined_lower):
            positive_score += 2
            break

    if re.search(KEY_SIGNATURE_PATTERN, combined_lower):
        positive_score += 1

    for pattern in SHARING_LANGUAGE:
        if re.search(pattern, combined_lower):
            positive_score += 2
            break

    if re.search(STYLE_TAG_DENSE_PATTERN, content_lower):
        positive_score += 2

    if positive_score < 2:
        return False, f"无Prompt内容信号 (得分={positive_score})"

    negative_score = 0
    negative_reasons = []

    fp_count = sum(1 for p in FIRST_PERSON_PATTERNS if re.search(p, content_lower))
    if fp_count >= 4:
        negative_score += 3
        negative_reasons.append(f"第一人称过密({fp_count}处)")
    elif fp_count >= 2:
        negative_score += 1

    disc_count = sum(1 for d in DISCUSSION_WORDS if re.search(d, content_lower))
    if disc_count >= 2:
        negative_score += 2
        negative_reasons.append(f"讨论吐槽词({disc_count}处)")
    elif disc_count >= 1:
        negative_score += 1

    net_score = positive_score - negative_score
    if net_score < 1:
        reasons = "; ".join(negative_reasons) if negative_reasons else "负信号过强"
        return False, f"非Prompt内容 ({reasons}, 净分={net_score})"

    comma_count = len(re.findall(r'[,，]', content))
    if comma_count < 5:
        return False, f"逗号不足 ({comma_count}个, 需>=5)"

    return True, ""


def calc_prompt_score(title: str, content: str) -> float:
    """
    计算「Prompt 质量」分数 (0~10)
    权重: 结构/技术信号35%, 效果词15%, 关键词15%, 方括号20%, 长度15%
    """
    combined = f"{title} {content}"
    combined_lower = combined.lower()

    strong_hits = 0
    content_l = content.lower()
    for pattern in STRUCTURE_META_TAGS:
        if re.search(pattern, content_l):
            strong_hits += 1
    if re.search(COMPOUND_TAG_PATTERN, content_l):
        strong_hits += 2
    for p in BPM_PATTERNS:
        if re.search(p, combined_lower):
            strong_hits += 1
            break
    if re.search(KEY_SIGNATURE_PATTERN, combined_lower):
        strong_hits += 1
    strong_score = min(strong_hits / 6, 1.0) * 10

    medium_hits = 0
    medium_patterns = [
        r"\b(?:reverb|delay|compression|sidechain|saturation|distortion|eq|filter)\b",
        r"\b(?:male|female)\s*(?:vocals?|singing|voice)\b",
        r"\b(?:upbeat|chill|dark|bright|energetic|melancholic|epic|cinematic)\b",
    ]
    for pattern in medium_patterns:
        if re.search(pattern, combined_lower):
            medium_hits += 1
    medium_score = (medium_hits / max(len(medium_patterns), 1)) * 10

    music_kw_hits = sum(1 for kw in MUSIC_KEYWORDS if kw in combined_lower)
    keyword_density = min(music_kw_hits / 15, 1.0) * 10

    bracket_count = len(re.findall(r"\[[^\]]+\]", combined))
    bracket_score = min(bracket_count / 5, 1.0) * 10

    length_score = 0
    content_len = len(content.strip())
    if 80 <= content_len <= 950:
        length_score = 10
    elif content_len >= 50:
        length_score = content_len / 95
    elif content_len > 950:
        length_score = max(0, 10 - (content_len - 950) / 100)

    final_score = (
        strong_score * 0.35 +
        medium_score * 0.15 +
        keyword_density * 0.15 +
        bracket_score * 0.20 +
        length_score * 0.15
    )

    return round(min(final_score, 10), 2)


def filter_and_score_posts(posts: list) -> List[dict]:
    """
    过滤 + 评分流水线：

    Step 0: is_real_prompt() 三层检测 (正信号/负信号/格式门槛)
    Step 1: is_junk_post() 垃圾标题检测
    Step 2: calc_prompt_score() 质量评分
    Step 3: 阈值过滤 (< MIN_PROMPT_SCORE)
    Step 4: 按质量分排序
    """
    min_score = float(os.getenv("MIN_PROMPT_SCORE", "4.0"))

    scored = []
    skipped_junk = 0
    skipped_no_prompt = 0
    skipped_low_score = 0

    for post in posts:
        title = post.get("title", "")
        content = post.get("content", "")

        is_prompt, reason = is_real_prompt(title, content)
        if not is_prompt:
            skipped_no_prompt += 1
            continue

        if is_junk_post(title):
            skipped_junk += 1
            continue

        score = calc_prompt_score(title, content)
        post["prompt_score"] = score

        if score < min_score:
            skipped_low_score += 1
            continue

        scored.append(post)

    scored.sort(key=lambda x: x["prompt_score"], reverse=True)

    print(f"    过滤: {skipped_no_prompt} 个非Prompt帖, {skipped_junk} 个垃圾帖, {skipped_low_score} 个低质量帖")
    print(f"    剩余 {len(scored)} 条高质量 Prompt")

    return scored


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_upvotes_from_rss(html_content: str) -> int:
    patterns = [
        r"(\d[\d,]*)\s*(?:points?|upvotes?|votes?)",
        r'"score"\s*:\s*(\d+)',
        r'"ups"\s*:\s*(\d+)',
        r"(\d+)\s*(?:points?\s*)?(?:\u2022|\u2022)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return -1


def _extract_author(entry: dict) -> str:
    author_raw = entry.get("author", "") or ""
    if isinstance(author_raw, dict):
        return author_raw.get("name", "unknown")
    match = re.search(r"/u(?:ser)?/([^/\s]+)", str(author_raw))
    if match:
        return match.group(1)
    return str(author_raw).split("@")[0].strip() or "unknown"


def select_top_prompts(posts: list, count: int = None) -> list:
    count = count or config.reddit.TARGET_COUNT
    return posts[:count]


def generate_issue_content(prompts: list) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# 📥 今日待翻译 Prompt ({today})",
        "",
        f"> 共 {len(prompts)} 条高质 Prompt 待翻译（已按 Prompt 质量分排序）",
        "> ",
        f"> 筛选标准: 非垃圾帖 + Prompt 质量分 >= 阈值",
        "> ",
        f"> 翻译完成后，请将内容添加到 `data/final_output/` 目录",
        "",
        "---",
        "",
    ]

    for i, p in enumerate(prompts, 1):
        lines.extend([
            f"## {i}. {p['title']}",
            "",
            "| 属性 | 值 |",
            "|------|-----|",
            f"| 🎯 Prompt质量分 | **{p.get('prompt_score', 0):.1f}**/10 |",
            f"| 👍 点赞数 | **{p['upvotes']}** |",
            f"| 📍 来源 | [r/{p['subreddit']}]({p['url']}) |",
            f"| 👤 作者 | u/{p['author']} |",
            f"| 🔗 数据源 | {p.get('source', 'unknown')} |",
            "",
            "**英文原文**:",
            "```",
            p["content"][:1500] + ("..." if len(p["content"]) > 1500 else ""),
            "```",
            "",
            "**中文翻译** (待填写):",
            "```",
            "",
            "```",
            "",
            "---",
            "",
        ])

    lines.extend([
        "## ✅ 完成检查清单",
        "",
        "- [ ] 翻译完成",
        "- [ ] 添加到对应流派文件",
        "- [ ] 更新 README 统计",
        "",
        "---",
        "",
        "*此 Issue 由 MUSICprompt 自动创建 v1.4.0 (Prompt 内容检测 v2)*",
    ])

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Reddit 音乐 Prompt 爬取器 v1.4.0")
    print("=" * 60)

    subreddits = config.reddit.SUBREDDITS
    target_count = config.reddit.TARGET_COUNT

    print(f"\n配置:")
    print(f"  子版块:     {', '.join(subreddits)}")
    print(f"  目标数量:   {target_count}")
    print(f"  最小质量分: {os.getenv('MIN_PROMPT_SCORE', '4.0')}")
    print(f"  数据策略:   RSS 优先 → JSON 备用")
    print()

    all_posts = []
    for subreddit in subreddits:
        print(f"获取 r/{subreddit}...")
        posts = fetch_reddit_posts(subreddit)
        all_posts.extend(posts)

    print(f"\n原始获取: {len(all_posts)} 条帖子")

    if not all_posts:
        print("\n⚠️ 未获取到任何帖子，可能原因:")
        print("  1. 网络无法访问 Reddit（尝试 VPN 或代理）")
        print("  2. 子版块暂时无活跃内容")
        print("\n💡 提示: GitHub Actions CI 环境通常会成功获取 JSON 数据")
        return

    print(f"\n{'=' * 60}")
    print("Phase 1: Prompt 检测与质量评分")
    print("=" * 60)

    scored_posts = filter_and_score_posts(all_posts)

    if not scored_posts:
        print("\n❌ 所有帖子均未达到 Prompt 质量标准")
        return

    top_prompts = select_top_prompts(scored_posts)

    print(f"\n最终选中 {len(top_prompts)} 条:")
    for i, p in enumerate(top_prompts, 1):
        print(f"  {i}. [{p['prompt_score']:.1f}分] [{p['upvotes']}👍] {p['title'][:55]}...")

    issue_content = generate_issue_content(top_prompts)

    output_dir = Path(__file__).parent.parent / "prompts" / "pending"
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"pending_{today}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(issue_content)

    print(f"\n✅ 已生成: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
