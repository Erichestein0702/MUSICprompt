#!/usr/bin/env python3
"""
Reddit 高赞 Prompt 爬取器
每日爬取 Reddit 上 7 条高赞音乐 Prompt，生成待翻译内容
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


def fetch_reddit_posts(subreddit: str, limit: int = 20, min_upvotes: int = 50) -> list:
    """获取 Reddit 热门帖子"""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    
    headers = {
        'User-Agent': 'MUSICprompt-Bot/1.0 (by MUSICprompt-team)'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        posts = []
        for child in data['data']['children']:
            post = child['data']
            if post['score'] >= min_upvotes and post.get('selftext'):
                posts.append({
                    'id': post['id'],
                    'title': post['title'],
                    'content': post['selftext'],
                    'upvotes': post['score'],
                    'author': post.get('author', 'unknown'),
                    'url': f"https://reddit.com{post['permalink']}",
                    'subreddit': subreddit,
                    'created_utc': post['created_utc']
                })
        
        return posts
    except Exception as e:
        print(f"获取 r/{subreddit} 失败: {e}")
        return []


def select_top_prompts(posts: list, count: int = 7) -> list:
    """选择点赞最高的 N 条"""
    sorted_posts = sorted(posts, key=lambda x: x['upvotes'], reverse=True)
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
        ""
    ]
    
    for i, prompt in enumerate(prompts, 1):
        lines.extend([
            f"## {i}. {prompt['title']}",
            "",
            f"| 属性 | 值 |",
            f"|------|-----|",
            f"| 👍 点赞数 | **{prompt['upvotes']}** |",
            f"| 📍 来源 | [r/{prompt['subreddit']}]({prompt['url']}) |",
            f"| 👤 作者 | u/{prompt['author']} |",
            "",
            "**英文原文**:",
            "```",
            prompt['content'][:1500] + ("..." if len(prompt['content']) > 1500 else ""),
            "```",
            "",
            "**中文翻译** (待填写):",
            "```",
            "",
            "```",
            "",
            "---",
            ""
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
        "*此 Issue 由 MUSICprompt 自动创建*"
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("Reddit 高赞 Prompt 爬取器")
    print("=" * 60)
    
    subreddits = ["SunoAI", "Udio", "aiMusic"]
    min_upvotes = int(os.getenv("MIN_UPVOTES", "50"))
    target_count = int(os.getenv("TARGET_COUNT", "7"))
    
    all_posts = []
    for subreddit in subreddits:
        print(f"\n获取 r/{subreddit}...")
        posts = fetch_reddit_posts(subreddit, limit=30, min_upvotes=min_upvotes)
        print(f"  找到 {len(posts)} 条符合条件的帖子")
        all_posts.extend(posts)
    
    top_prompts = select_top_prompts(all_posts, count=target_count)
    
    if not top_prompts:
        print("\n没有找到符合条件的帖子")
        return
    
    print(f"\n选中 {len(top_prompts)} 条最高赞内容:")
    for i, p in enumerate(top_prompts, 1):
        print(f"  {i}. [{p['upvotes']}👍] {p['title'][:50]}...")
    
    issue_content = generate_issue_content(top_prompts)
    
    output_dir = Path(__file__).parent.parent / "prompts" / "pending"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"pending_{today}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(issue_content)
    
    print(f"\n已生成待翻译文件: {output_file}")
    
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"issue_title=📥 今日待翻译 Prompt ({today})\n")
            issue_content_escaped = issue_content.replace('"', '\\"').replace('\n', '\\n')
            f.write(f'issue_content<<EOF\n{issue_content}\nEOF\n')
    
    print("=" * 60)


if __name__ == "__main__":
    main()
