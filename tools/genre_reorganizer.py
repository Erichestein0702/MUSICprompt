#!/usr/bin/env python3
"""
MUSICprompt 流派层级重组脚本

将扁平的流派文件重组为层级文件夹结构：
- Electronic > house, techno, trance, ambient, lo-fi
- Hip-Hop > trap, rap, lo-fi hip hop, boom bap
- Rock > metal, punk, indie
- 独立顶级流派: pop, jazz, classical, folk, country, soul, r&b, blues, funk
- Else: 未分类

Usage:
    python tools/genre_reorganizer.py [--dry-run]
"""

import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


GENRE_HIERARCHY = {
    'electronic': {
        'name': 'Electronic',
        'name_zh': '电子音乐',
        'sub_genres': ['house', 'techno', 'trance', 'ambient', 'lo-fi'],
        'description': '电子音乐合集，包含 House、Techno、Trance、Ambient 等子流派'
    },
    'hip-hop': {
        'name': 'Hip-Hop',
        'name_zh': '嘻哈',
        'sub_genres': ['trap', 'rap', 'hip hop', 'lo-fi hip hop', 'boom bap', 'old school'],
        'description': '嘻哈音乐合集，包含 Trap、Rap、Lo-fi Hip Hop 等子流派'
    },
    'rock': {
        'name': 'Rock',
        'name_zh': '摇滚',
        'sub_genres': ['metal', 'punk', 'indie', 'alternative', 'emo'],
        'description': '摇滚音乐合集，包含 Metal、Punk、Indie 等子流派'
    }
}

STANDALONE_GENRES = {
    'pop': {'name': 'Pop', 'name_zh': '流行'},
    'jazz': {'name': 'Jazz', 'name_zh': '爵士'},
    'classical': {'name': 'Classical', 'name_zh': '古典'},
    'folk': {'name': 'Folk', 'name_zh': '民谣'},
    'country': {'name': 'Country', 'name_zh': '乡村'},
    'soul': {'name': 'Soul', 'name_zh': '灵魂'},
    'r&b': {'name': 'R&B', 'name_zh': '节奏布鲁斯'},
    'blues': {'name': 'Blues', 'name_zh': '布鲁斯'},
    'funk': {'name': 'Funk', 'name_zh': '放克'}
}

GENRE_ALIASES = {
    'hip hop': 'hip-hop',
    'lo-fi': 'lo-fi',
    'lo-fi hip hop': 'hip-hop',
    'r&b': 'r&b',
    'rnb': 'r&b',
}


class GenreReorganizer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.genres_dir = project_root / "data" / "final_output" / "genres"
        self.curated_dir = project_root / "data" / "final_output" / "curated"
        self.processed_dir = project_root / "data" / "processed" / "extracted"
        self.new_genres_dir = project_root / "data" / "final_output" / "genres_new"
        self.genre_mapping: Dict[str, str] = {}
        
    def load_all_prompts(self) -> List[Dict]:
        prompts = []
        translated_file = self.processed_dir / "translated_prompts.json"
        if translated_file.exists():
            with open(translated_file, 'r', encoding='utf-8') as f:
                prompts.extend(json.load(f))
        return prompts
    
    def normalize_genre(self, genre: str) -> str:
        genre_lower = genre.lower().strip()
        return GENRE_ALIASES.get(genre_lower, genre_lower)
    
    def get_parent_genre(self, genre: str) -> str:
        genre_norm = self.normalize_genre(genre)
        for parent, info in GENRE_HIERARCHY.items():
            if genre_norm in [self.normalize_genre(g) for g in info['sub_genres']]:
                return parent
            if genre_norm == parent:
                return parent
        if genre_norm in [self.normalize_genre(g) for g in STANDALONE_GENRES.keys()]:
            return genre_norm
        return 'else'
    
    def classify_prompts(self, prompts: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
        classified = defaultdict(lambda: defaultdict(list))
        
        for prompt in prompts:
            genres = prompt.get('genre', [])
            if not genres:
                classified['else']['uncategorized'].append(prompt)
                continue
            
            primary_genre = self.normalize_genre(genres[0])
            parent = self.get_parent_genre(primary_genre)
            
            if parent in GENRE_HIERARCHY:
                if primary_genre in [self.normalize_genre(g) for g in GENRE_HIERARCHY[parent]['sub_genres']]:
                    sub_genre = primary_genre
                else:
                    sub_genre = 'other'
                classified[parent][sub_genre].append(prompt)
            elif parent in STANDALONE_GENRES:
                classified[parent][parent].append(prompt)
            else:
                classified['else'][primary_genre].append(prompt)
        
        return dict(classified)
    
    def create_genre_structure(self, dry_run: bool = False):
        print("=" * 60)
        print("MUSICprompt 流派层级重组")
        print("=" * 60)
        
        prompts = self.load_all_prompts()
        print(f"\n加载了 {len(prompts)} 条提示词")
        
        classified = self.classify_prompts(prompts)
        
        print("\n分类结果预览:")
        for parent, sub_genres in sorted(classified.items()):
            total = sum(len(p) for p in sub_genres.values())
            print(f"  {parent}: {total} 条")
            for sub, items in sorted(sub_genres.items()):
                if sub != parent:
                    print(f"    └─ {sub}: {len(items)} 条")
        
        if dry_run:
            print("\n[DRY RUN] 不执行实际操作")
            return
        
        if self.new_genres_dir.exists():
            shutil.rmtree(self.new_genres_dir)
        self.new_genres_dir.mkdir(parents=True)
        
        for parent, sub_genres in classified.items():
            if parent in GENRE_HIERARCHY:
                parent_dir = self.new_genres_dir / parent
                parent_dir.mkdir(exist_ok=True)
                
                all_parent_prompts = []
                for sub_genre, items in sub_genres.items():
                    all_parent_prompts.extend(items)
                    
                    if sub_genre != 'other':
                        sub_dir = parent_dir / sub_genre
                        sub_dir.mkdir(exist_ok=True)
                        self._save_genre_files(sub_dir, sub_genre, items)
                
                self._save_genre_files(parent_dir, parent, all_parent_prompts, is_parent=True)
                
            elif parent in STANDALONE_GENRES:
                genre_dir = self.new_genres_dir / parent
                genre_dir.mkdir(exist_ok=True)
                items = list(sub_genres.values())[0] if sub_genres else []
                self._save_genre_files(genre_dir, parent, items)
                
            else:
                else_dir = self.new_genres_dir / "else"
                else_dir.mkdir(exist_ok=True)
                all_else = []
                for sub, items in sub_genres.items():
                    all_else.extend(items)
                self._save_genre_files(else_dir, "uncategorized", all_else)
        
        print(f"\n新结构已创建: {self.new_genres_dir}")
        
        backup_dir = self.genres_dir.parent / "genres_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(self.genres_dir), str(backup_dir))
        print(f"旧文件已备份: {backup_dir}")
        
        shutil.move(str(self.new_genres_dir), str(self.genres_dir))
        print(f"新结构已应用: {self.genres_dir}")
        
        self._reorganize_curated(classified)
        
        print("\n" + "=" * 60)
        print("流派层级重组完成!")
        print("=" * 60)
    
    def _save_genre_files(self, target_dir: Path, genre_name: str, prompts: List[Dict], is_parent: bool = False):
        if not prompts:
            return
        
        sorted_prompts = sorted(prompts, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        json_file = target_dir / f"{genre_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_prompts, f, ensure_ascii=False, indent=2)
        
        md_content = self._generate_genre_markdown(genre_name, sorted_prompts, is_parent)
        md_file = target_dir / f"{genre_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"  生成: {target_dir.relative_to(self.project_root)} ({len(prompts)} 条)")
    
    def _generate_genre_markdown(self, genre_name: str, prompts: List[Dict], is_parent: bool = False) -> str:
        genre_info = GENRE_HIERARCHY.get(genre_name, STANDALONE_GENRES.get(genre_name, {}))
        display_name = genre_info.get('name', genre_name.title())
        display_name_zh = genre_info.get('name_zh', genre_name.title())
        
        lines = [
            f"# {display_name} / {display_name_zh}",
            "",
            f"> 共收录 {len(prompts)} 条提示词",
            ""
        ]
        
        if is_parent and genre_name in GENRE_HIERARCHY:
            sub_genres = GENRE_HIERARCHY[genre_name]['sub_genres']
            lines.append("## 子流派 / Sub-genres")
            lines.append("")
            for sub in sub_genres:
                sub_dir = Path(genre_name) / sub
                lines.append(f"- [{sub.title()}](./{sub}/{sub}.md)")
            lines.append("")
        
        lines.extend([
            "## 提示词列表 / Prompt List",
            ""
        ])
        
        for i, prompt in enumerate(prompts, 1):
            title = prompt.get('title', f'Prompt #{i}')
            score = prompt.get('quality_score', 0)
            prompt_text = prompt.get('prompt_text', '')
            prompt_zh = prompt.get('prompt_zh', '')
            genres = prompt.get('genre', [])
            instruments = prompt.get('instruments', [])
            
            lines.append(f"### {i}. {title}")
            lines.append(f"**评分**: {score}/10")
            lines.append(f"**流派**: {', '.join(genres) if genres else '未分类'}")
            lines.append("")
            
            if instruments:
                lines.append(f"**乐器**: {', '.join(instruments)}")
            lines.append("")
            
            lines.append("<details>")
            lines.append("<summary>点击展开查看完整提示词</summary>")
            lines.append("")
            lines.append("#### 英文提示词")
            lines.append("```")
            lines.append(prompt_text)
            lines.append("```")
            lines.append("")
            
            if prompt_zh:
                lines.append("")
                lines.append("#### 中文翻译")
                lines.append("```")
                lines.append(prompt_zh)
                lines.append("```")
                lines.append("")
            
            lines.append("</details>")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _reorganize_curated(self, classified: Dict):
        print("\n重组精校目录...")
        
        new_curated_dir = self.curated_dir.parent / "curated_new"
        if new_curated_dir.exists():
            shutil.rmtree(new_curated_dir)
        new_curated_dir.mkdir(parents=True)
        
        all_curated = []
        for parent, sub_genres in classified.items():
            for sub, items in sub_genres.items():
                curated_items = [p for p in items if p.get('quality_score', 0) >= 8]
                if not curated_items:
                    continue
                
                all_curated.extend(curated_items)
                
                if parent in GENRE_HIERARCHY:
                    parent_dir = new_curated_dir / parent
                    parent_dir.mkdir(exist_ok=True)
                    
                    if sub != 'other':
                        self._save_curated_files(parent_dir, sub, curated_items)
                else:
                    self._save_curated_files(new_curated_dir, parent if parent != 'else' else 'uncategorized', curated_items)
        
        self._save_curated_files(new_curated_dir, 'all', all_curated, is_index=True)
        
        backup_dir = self.curated_dir.parent / "curated_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(self.curated_dir), str(backup_dir))
        shutil.move(str(new_curated_dir), str(self.curated_dir))
        
        print(f"精校目录已重组: {self.curated_dir}")
    
    def _save_curated_files(self, target_dir: Path, genre_name: str, prompts: List[Dict], is_index: bool = False):
        if not prompts and not is_index:
            return
        
        sorted_prompts = sorted(prompts, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        if is_index:
            json_file = target_dir / "all_curated.json"
            md_file = target_dir / "README.md"
        else:
            json_file = target_dir / f"{genre_name}_curated.json"
            md_file = target_dir / f"{genre_name}_curated.md"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_prompts, f, ensure_ascii=False, indent=2)
        
        md_content = self._generate_genre_markdown(genre_name, sorted_prompts, is_index)
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)


def main():
    parser = argparse.ArgumentParser(description="MUSICprompt 流派层级重组脚本")
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不执行实际操作')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    reorganizer = GenreReorganizer(project_root)
    reorganizer.create_genre_structure(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
