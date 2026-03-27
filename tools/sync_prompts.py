#!/usr/bin/env python3
"""
同步 Prompts 目录
将 data/final_output 中的 MD 文件同步到 prompts/ 目录
"""

import shutil
from pathlib import Path


def sync_prompts():
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "data" / "final_output"
    target_dir = project_root / "prompts"
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    (target_dir / "curated").mkdir(parents=True, exist_ok=True)
    (target_dir / "genres").mkdir(parents=True, exist_ok=True)
    (target_dir / "use_cases").mkdir(parents=True, exist_ok=True)
    (target_dir / "pending").mkdir(parents=True, exist_ok=True)
    
    curated_source = source_dir / "curated"
    curated_target = target_dir / "curated"
    
    if curated_source.exists():
        for md_file in curated_source.rglob("*.md"):
            rel_path = md_file.relative_to(curated_source)
            target_file = curated_target / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, target_file)
            print(f"  复制: {rel_path}")
    
    genres_source = source_dir / "genres"
    genres_target = target_dir / "genres"
    
    if genres_source.exists():
        for md_file in genres_source.rglob("*.md"):
            rel_path = md_file.relative_to(genres_source)
            target_file = genres_target / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, target_file)
            print(f"  复制: genres/{rel_path}")
    
    use_cases_source = source_dir / "use_cases"
    use_cases_target = target_dir / "use_cases"
    
    if use_cases_source.exists():
        for md_file in use_cases_source.glob("*.md"):
            target_file = use_cases_target / md_file.name
            shutil.copy2(md_file, target_file)
            print(f"  复制: use_cases/{md_file.name}")
    
    print("\n同步完成!")


if __name__ == "__main__":
    print("=" * 60)
    print("同步 Prompts 目录")
    print("=" * 60)
    sync_prompts()
