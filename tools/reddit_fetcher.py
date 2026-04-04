#!/usr/bin/env python3
"""
Reddit 音乐 Prompt 爬取器 v1.3.0

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
                "User-Agent": "MUSICprompt-RSS/1.3.0 (by /u/MUSICprompt-team)"
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
                "User-Agent": "MUSICprompt-Bot/1.3.0 (by /u/MUSICprompt-team)"
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
# ============================================================

# 标题中的垃圾帖模式（匹配即丢弃）
JUNK_TITLE_PATTERNS = [
    r"\?",                                    # 含问号
    r"(?i)\bhelp\b",                          # help
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

# 正文中的强 Prompt 特征信号
PROMPT_SIGNALS_STRONG = [
    # 结构标签（最强信号）
    r"\[(?:intro|verse|chorus|bridge|outro|hook|solo|build|drop|pre-chorus|interlude|break)\]",
    # BPM 格式
    r"\b(?:bpm|tempo)\s*[:\-]?\s*\d{2,3}\b",
    # 调性格式
    r"\b(?:key|scale)\s*[:\-]?\s*[a-g][#]?\s*(?:major|minor|maj|min)\b",
    # 方括号风格标签 [genre], [style]
    r"\[[^\]]{2,20}\](?:\s*\[[^\]]{2,20}\])+",  # 连续多个方括号标签
]

# 中等信号
PROMPT_SIGNALS_MEDIUM = [
    r"\b(?:reverb|delay|compression|sidechain|saturation|distortion|eq|filter)\b",
    r"\b(?:male|female)\s*(?:vocals?|singing|voice)\b",
    r"\b(?:upbeat|chill|dark|bright|energetic|melancholic|epic|cinematic)\b",
    r"\b\d+\s*(?:bpm|BPM)\b",
]


def is_junk_post(title: str) -> bool:
    """判断是否为垃圾帖（求助/讨论/问题等非 Prompt 内容）"""
    for pattern in JUNK_TITLE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False


def is_real_prompt(title: str, content: str) -> Tuple[bool, str]:
    """
    硬性门槛：判断是否包含真正的音乐 Prompt 文本

    必须同时满足：
      1. 标题或正文中含 'prompt' 关键词（不区分大小写）
      2. 正文中有 5 个以上英文逗号或中文逗号（结构化内容的标志）

    返回: (是否通过, 原因说明)
    """
    combined = f"{title} {content}"
    combined_lower = combined.lower()

    has_prompt_keyword = bool(re.search(r'\bprompt\b', combined_lower))
    if not has_prompt_keyword:
        return False, "缺少 prompt 关键词"

    comma_count = len(re.findall(r'[,，]', content))
    if comma_count < 5:
        return False, f"逗号不足 ({comma_count}个, 需≥5)"

    return True, ""


def calc_prompt_score(title: str, content: str) -> float:
    """
    计算「Prompt 质量」分数 (0~10)

    这个分数衡量的是：这篇帖子有多大概率是一个真正的音乐生成 Prompt，
    而不是普通的讨论/分享/求助。

    权重分配：
      - 强信号（结构标签/BPM/调性）：50%   ← 有这些基本确定是 Prompt
      - 中等信号（效果词/乐器/情绪）：30%
      - 音乐关键词密度：20%
    """
    combined = f"{title} {content}"
    combined_lower = combined.lower()

    strong_hits = 0
    total_strong = len(PROMPT_SIGNALS_STRONG)
    for pattern in PROMPT_SIGNALS_STRONG:
        if re.search(pattern, combined_lower):
            strong_hits += 1
    strong_score = (strong_hits / max(total_strong, 1)) * 10 if total_strong else 0

    medium_hits = 0
    total_medium = len(PROMPT_SIGNALS_MEDIUM)
    for pattern in PROMPT_SIGNALS_MEDIUM:
        if re.search(pattern, combined_lower):
            medium_hits += 1
    medium_score = (medium_hits / max(total_medium, 1)) * 10 if total_medium else 0

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

    Step 0: 硬性门槛 — 必须含 'prompt' 关键词 + ≥5 个逗号
    Step 1: 去掉标题为垃圾帖的
    Step 2: 计算每篇的 Prompt 质量分
    Step 3: 过滤掉低于阈值的质量分
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

        # Step 0: 硬性门槛 — 必须是真正的 Prompt 文本
        is_prompt, reason = is_real_prompt(title, content)
        if not is_prompt:
            skipped_no_prompt += 1
            continue

        # Step 1: 垃圾帖直接丢掉
        if is_junk_post(title):
            skipped_junk += 1
            continue

        # Step 2: 计算 Prompt 质量分
        score = calc_prompt_score(title, content)
        post["prompt_score"] = score

        # Step 3: 低于阈值的过滤
        if score < min_score:
            skipped_low_score += 1
            continue

        scored.append(post)

    # Step 4: 按 Prompt 质量分降序排列
    scored.sort(key=lambda x: x["prompt_score"], reverse=True)

    print(f"    过滤: {skipped_no_prompt} 个非Prompt帖, {skipped_junk} 个垃圾帖, {skipped_low_score} 个低质量帖")
    print(f"    剩余 {len(scored)} 条高质量 Prompt")

    return scored


# ============================================================
# 辅助函数
# ============================================================

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
    """从 RSS HTML 内容中尽力提取点赞数"""
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


# ============================================================
# 输出
# ============================================================

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
        f"> 筛选标准: 非垃圾帖 + Prompt 质量分 ≥ 阈值",
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
        "*此 Issue 由 MUSICprompt 自动创建 v1.3.0 (Prompt 质量筛选)*",
    ])

    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("Reddit 音乐 Prompt 爬取器 v1.3.0")
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
