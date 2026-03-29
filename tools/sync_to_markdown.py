#!/usr/bin/env python3
"""
Markdown 同步脚本
从 SQLite 数据库生成 Markdown 文件，推送到 GitHub
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models import MusicPromptDB


GENRE_ICONS = {
    "pop": "🎤",
    "rock": "🎸",
    "electronic": "🎹",
    "hip-hop": "🎤",
    "rap": "🎤",
    "jazz": "🎷",
    "blues": "🎵",
    "classical": "🎻",
    "folk": "🪕",
    "country": "🤠",
    "r&b": "🎶",
    "soul": "🎺",
    "funk": "🎸",
    "metal": "🤘",
    "punk": "🎸",
    "ambient": "🌙",
    "lo-fi": "📻",
    "house": "🏠",
    "techno": "🎛️",
    "trap": "🎯",
    "dubstep": "💥",
    "trance": "✨",
}

USE_CASE_NAMES = {
    "party": "派对聚会",
    "study": "学习专注",
    "gaming": "游戏电竞",
    "cinematic": "影视配乐",
    "meditation": "冥想放松",
    "workout": "健身运动",
    "sleep": "睡眠休息",
    "general": "通用场景",
}


def generate_genre_markdown(prompts: List[Dict], genre: str) -> str:
    """生成流派 Markdown 文件"""
    icon = GENRE_ICONS.get(genre, "🎵")
    
    lines = [
        f"# {icon} {genre.upper()} 音乐提示词",
        "",
        f"> 共收录 {len(prompts)} 条提示词",
        "",
        "---",
        "",
    ]
    
    for i, p in enumerate(prompts, 1):
        score = p.get('quality_score', 0)
        lines.extend([
            f"### {i}. {p.get('title', '未命名')}",
            "",
            f"**评分**: {score}/10",
            "",
        ])
        
        if p.get('bpm') or p.get('key_signature'):
            lines.append("**技术参数**:")
            if p.get('bpm'):
                lines.append(f"- BPM: {p['bpm']}")
            if p.get('key_signature'):
                lines.append(f"- 调性: {p['key_signature']}")
            lines.append("")
        
        lines.extend([
            "#### 英文提示词",
            "```",
            p.get('prompt_text', ''),
            "```",
            "",
        ])
        
        if p.get('prompt_zh'):
            lines.extend([
                "#### 中文翻译",
                "```",
                p['prompt_zh'],
                "```",
                "",
            ])
        
        lines.extend(["---", ""])
    
    return "\n".join(lines)


def generate_use_case_markdown(prompts: List[Dict], use_case: str) -> str:
    """生成使用场景 Markdown 文件"""
    cn_name = USE_CASE_NAMES.get(use_case, use_case)
    
    lines = [
        f"# {cn_name} 音乐提示词",
        "",
        f"> 共收录 {len(prompts)} 条适合{cn_name}场景的提示词",
        "",
        "---",
        "",
    ]
    
    for i, p in enumerate(prompts[:20], 1):
        lines.extend([
            f"### {i}. {p.get('title', '未命名')}",
            "",
            f"**评分**: {p.get('quality_score', 0)}/10",
            "",
            "#### 英文提示词",
            "```",
            p.get('prompt_text', ''),
            "```",
            "",
        ])
        
        if p.get('prompt_zh'):
            lines.extend([
                "#### 中文翻译",
                "```",
                p['prompt_zh'],
                "```",
                "",
            ])
        
        lines.extend(["---", ""])
    
    return "\n".join(lines)


def generate_index_markdown(stats: Dict) -> str:
    """生成索引页 Markdown"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    lines = [
        "# 📁 Prompts 目录",
        "",
        f"> 最后更新: {today}",
        "",
        "## 📊 数据统计",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 总 Prompt 数 | **{stats['total_prompts']}** |",
        f"| 流派数 | **{stats['total_genres']}** |",
        f"| 乐器数 | **{stats['total_instruments']}** |",
        f"| 使用场景数 | **{stats['total_use_cases']}** |",
        f"| 平均评分 | **{stats['avg_quality_score']}** |",
        "",
        "---",
        "",
        "## 🎵 按流派浏览",
        "",
        "| 流派 | 数量 | 链接 |",
        "|------|------|------|",
    ]
    
    for g in stats['top_genres']:
        icon = GENRE_ICONS.get(g['name'], "🎵")
        lines.append(
            f"| {icon} {g['name']} | {g['count']} | [查看](genres/{g['name']}.md) |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 🎯 按场景浏览",
        "",
        "| 场景 | 链接 |",
        "|------|------|",
    ])
    
    for uc_key, uc_name in USE_CASE_NAMES.items():
        lines.append(f"| {uc_name} | [查看](use_cases/{uc_key}.md) |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔍 检索工具",
        "",
        "使用本地检索工具进行高级搜索：",
        "",
        "```bash",
        "python tools/search_prompts.py --query \"关键词\"",
        "python tools/search_prompts.py --genre pop --min-score 8",
        "```",
        "",
    ])
    
    return "\n".join(lines)


def sync_to_markdown(db_path: str = "data/musicprompts.db", output_dir: str = "prompts"):
    """同步数据库到 Markdown 文件"""
    project_root = Path(__file__).parent.parent
    output_path = project_root / output_dir
    
    print("=" * 60)
    print("Markdown 同步")
    print("=" * 60)
    
    db = MusicPromptDB(str(project_root / db_path))
    
    stats = db.get_stats()
    print(f"数据库统计: {stats['total_prompts']} 条 Prompt")
    
    index_content = generate_index_markdown(stats)
    index_file = output_path / "README.md"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"生成索引: {index_file}")
    
    genres_dir = output_path / "genres"
    genres_dir.mkdir(parents=True, exist_ok=True)
    
    for genre_info in stats['top_genres']:
        genre_name = genre_info['name']
        prompts = db.get_prompts_by_genre(genre_name, limit=100)
        if prompts:
            content = generate_genre_markdown(prompts, genre_name)
            genre_file = genres_dir / f"{genre_name}.md"
            with open(genre_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"生成流派: {genre_name} ({len(prompts)} 条)")
    
    use_cases_dir = output_path / "use_cases"
    use_cases_dir.mkdir(parents=True, exist_ok=True)
    
    for uc_key in USE_CASE_NAMES.keys():
        prompts = db.get_prompts_by_use_case(uc_key, limit=50)
        if prompts:
            content = generate_use_case_markdown(prompts, uc_key)
            uc_file = use_cases_dir / f"{uc_key}.md"
            with open(uc_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"生成场景: {uc_key} ({len(prompts)} 条)")
    
    top_prompts = db.get_top_prompts(limit=20)
    if top_prompts:
        content = generate_genre_markdown(top_prompts, "精选")
        curated_file = output_path / "curated.md"
        with open(curated_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"生成精选: {len(top_prompts)} 条")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("同步完成!")
    print("=" * 60)


if __name__ == "__main__":
    sync_to_markdown()
