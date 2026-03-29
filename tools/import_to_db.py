#!/usr/bin/env python3
"""
数据导入脚本
将现有 JSON 数据导入到 SQLite 数据库
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models import MusicPromptDB


def load_json_files(data_dir: Path) -> list:
    """加载所有 JSON 数据文件"""
    all_prompts = []
    
    curated_dir = data_dir / "final_output" / "curated"
    if curated_dir.exists():
        for json_file in curated_dir.rglob("*.json"):
            if json_file.name == "all_curated.json":
                continue
            print(f"加载: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_prompts.extend(data)
    
    genres_dir = data_dir / "final_output" / "genres"
    if genres_dir.exists():
        for json_file in genres_dir.rglob("*.json"):
            print(f"加载: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_prompts.extend(data)
    
    return all_prompts


def import_data(db_path: str = "data/musicprompts.db"):
    """导入数据到数据库"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print("=" * 60)
    print("MUSICprompt 数据导入")
    print("=" * 60)
    
    db = MusicPromptDB(db_path)
    db.init_db()
    
    prompts = load_json_files(data_dir)
    print(f"\n共加载 {len(prompts)} 条 Prompt")
    
    success = 0
    failed = 0
    
    for i, prompt in enumerate(prompts, 1):
        if db.insert_prompt(prompt):
            success += 1
        else:
            failed += 1
        
        if i % 100 == 0:
            print(f"进度: {i}/{len(prompts)}")
    
    print(f"\n导入完成: 成功 {success}, 失败 {failed}")
    
    stats = db.get_stats()
    print("\n数据库统计:")
    print(f"  总 Prompt 数: {stats['total_prompts']}")
    print(f"  流派数: {stats['total_genres']}")
    print(f"  乐器数: {stats['total_instruments']}")
    print(f"  使用场景数: {stats['total_use_cases']}")
    print(f"  平均评分: {stats['avg_quality_score']}")
    print(f"\n热门流派:")
    for g in stats['top_genres'][:5]:
        print(f"  {g['name']}: {g['count']} 条")
    
    db.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import_data()
