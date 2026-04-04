#!/usr/bin/env python3
"""
Reddit RSS Feed 爬取器（替代原 urllib JSON API 方案）

使用 Reddit 公开 RSS Feed 获取高赞音乐 Prompt，无需 OAuth 认证。
RSS Feed 是 Reddit 官方提供的公开接口，稳定且合规。

数据源示例：
  https://www.reddit.com/r/SunoAI/.rss
  https://www.reddit.com/r/Udio/.rss
  https://www.reddit.com/r/aiMusic/.rss
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import feedparser
except ImportError:
    print("错误: 缺少 feedparser 依赖")
    print("请运行: pip install feedparser")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config


def fetch_reddit_rss(subreddit: str, limit: int = 25) -> list:
    """通过 RSS Feed 获取 Reddit 子版块帖子"""
    url = config.reddit.RSS_FEED_URL_TEMPLATE.format(subreddit=subreddit)

    try:
        feed = feedparser.parse(
            url,
            request_headers={
                "User-Agent": "MUSICprompt-RSS/2.0 (by /u/MUSICprompt-team)"
            },
        )

        if not feed or feed.bozo:
            print(f"  r/{subreddit}: RSS 解析失败或无内容")
            if hasattr(feed, "bozo_exception"):
                print(f"    原因: {feed.bozo_exception}")
            return []

        posts = []
        for entry in feed.entries[:limit]:
            post = _parse_rss_entry(entry, subreddit)
            if post:
                posts.append(post)

        print(f"  r/{subreddit}: 通过 RSS 获取 {len(posts)} 条帖子")
        return posts

    except Exception as e:
        print(f"  r/{subreddit} RSS 获取异常: {e}")
        return []


def _parse_rss_entry(entry: dict, subreddit: str) -> Optional[dict]:
    """解析单条 RSS entry 为标准格式"""
    content_raw = entry.get("summary", "") or entry.get("description", "") or ""

    upvotes = _extract_upvotes(content_raw)
    if upvotes < config.reddit.MIN_UPVOTES and upvotes >= 0:
        return None

    title = _clean_html(entry.get("title", ""))
    content = _clean_html(content_raw)

    if not content or len(content.strip()) < 20:
        return None

    return {
        "id": entry.get("id", "").split("/")[-1] or "",
        "title": title,
        "content": content[:2000],
        "upvotes": max(upvotes, 0),
        "author": _extract_author(entry),
        "url": entry.get("link", ""),
        "subreddit": subreddit,
        "created_utc": _parse_published(entry.get("published", "")),
    }


def _extract_upvotes(content: str) -> int:
    """从 RSS 内容中提取点赞数"""
    patterns = [
        r"(\d[\d,]*)\s*(?:points?|upvotes?|votes?|👍)",
        r"(?:points?|upvotes?|votes?|👍)\s*:?\s*(\d[\d,]*)",
        r'"score"\s*:\s*(\d+)',
        r'"ups"\s*:\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return -1


def _extract_author(entry: dict) -> str:
    """从 RSS entry 中提取作者"""
    author_raw = entry.get("author", "") or ""
    if isinstance(author_raw, dict):
        return author_raw.get("name", "unknown")
    match = re.search(r"/u(?:ser)?/([^/\s]+)", str(author_raw))
    if match:
        return match.group(1)
    return str(author_raw).split("@")[0].strip() or "unknown"


def _parse_published(published_str: str) -> float:
    """解析发布时间为 unix timestamp"""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(published_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return datetime.now().timestamp()


def _clean_html(text: str) -> str:
    """清理 HTML 标签和多余空白"""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def select_top_prompts(posts: list, count: int = None) -> list:
    """选择点赞最高的 N 条"""
    count = count or config.reddit.TARGET_COUNT
    sorted_posts = sorted(posts, key=lambda x: x["upvotes"], reverse=True)
    return sorted_posts[:count]


def generate_issue_content(prompts: list) -> str:
    """生成 Issue 内容"""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# 📥 今日待翻译 Prompt ({today})",
        "",
        f"> 共 {len(prompts)} 条高赞内容待翻译",
        "> ",
        f"> 翻译完成后，请将内容添加到 `data/final_output/` 目录",
        "",
        "---",
        "",
    ]

    for i, prompt in enumerate(prompts, 1):
        lines.extend([
            f"## {i}. {prompt['title']}",
            "",
            "| 属性 | 值 |",
            "|------|-----|",
            f"| 👍 点赞数 | **{prompt['upvotes']}** |",
            f"| 📍 来源 | [r/{prompt['subreddit']}]({prompt['url']}) |",
            f"| 👤 作者 | u/{prompt['author']} |",
            "",
            "**英文原文**:",
            "```",
            prompt["content"][:1500] + ("..." if len(prompt["content"]) > 1500 else ""),
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
        "*此 Issue 由 MUSICprompt 自动创建 (RSS Feed 方式)*",
    ])

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Reddit RSS Feed 高赞 Prompt 爬取器 v2.0")
    print("=" * 60)

    subreddits = config.reddit.SUBREDDITS
    target_count = config.reddit.TARGET_COUNT

    print(f"\n配置:")
    print(f"  子版块:   {', '.join(subreddits)}")
    print(f"  目标数量: {target_count}")
    print(f"  数据方式: RSS Feed (无需 OAuth)")
    print()

    all_posts = []
    for subreddit in subreddits:
        print(f"获取 r/{subreddit}...")
        posts = fetch_reddit_rss(subreddit, limit=30)
        all_posts.extend(posts)

    print(f"\n总计获取 {len(all_posts)} 条帖子")

    if not all_posts:
        print("\n⚠️ 没有找到符合条件的帖子，可能原因：")
        print("  1. 子版块暂时没有活跃帖子")
        print("  2. RSS Feed 服务暂时不可用")
        print("  3. 当前时间所有帖子点赞数均低于阈值")
        print("\n💡 建议：稍后重试或降低 MIN_UPVOTES 阈值")
        return

    top_prompts = select_top_prompts(all_posts)

    print(f"\n选中 {len(top_prompts)} 条最高赞内容:")
    for i, p in enumerate(top_prompts, 1):
        print(f"  {i}. [{p['upvotes']}👍] {p['title'][:50]}...")

    issue_content = generate_issue_content(top_prompts)

    output_dir = (
        Path(__file__).parent.parent / "prompts" / "pending"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"pending_{today}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(issue_content)

    print(f"\n✅ 已生成待翻译文件: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
