#!/usr/bin/env python3
"""
MUSICprompt Automated Publishing Script

Usage:
    python tools/publish_update.py [--no-push] [--message "custom message"]
"""

import json
import csv
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class PublishManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.output_dir = self.data_dir / "final_output"
        self.processed_dir = self.data_dir / "processed"
    
    def load_all_prompts(self) -> List[Dict]:
        prompts = []
        translated_file = self.processed_dir / "extracted" / "translated_prompts.json"
        if translated_file.exists():
            with open(translated_file, 'r', encoding='utf-8') as f:
                prompts.extend(json.load(f))
        extracted_file = self.processed_dir / "extracted" / "extracted_prompts.json"
        if extracted_file.exists():
            with open(extracted_file, 'r', encoding='utf-8') as f:
                extracted = json.load(f)
                existing_ids = {p.get('id') for p in prompts}
                for p in extracted:
                    if p.get('id') not in existing_ids:
                        prompts.append(p)
        return prompts
    
    def generate_statistics(self, prompts: List[Dict]) -> Dict:
        stats = {
            'total_prompts': len(prompts),
            'curated_count': sum(1 for p in prompts if p.get('quality_score', 0) >= 8),
            'translated_count': sum(1 for p in prompts if p.get('prompt_zh')),
            'genre_distribution': {},
            'platform_distribution': {},
            'quality_distribution': {'excellent': 0, 'good': 0, 'average': 0},
            'use_case_distribution': {},
            'last_updated': datetime.now().isoformat()
        }
        for prompt in prompts:
            for genre in prompt.get('genre', []):
                stats['genre_distribution'][genre] = stats['genre_distribution'].get(genre, 0) + 1
            platform = prompt.get('platform', 'unknown')
            stats['platform_distribution'][platform] = stats['platform_distribution'].get(platform, 0) + 1
            score = prompt.get('quality_score', 0)
            if score >= 9:
                stats['quality_distribution']['excellent'] += 1
            elif score >= 7:
                stats['quality_distribution']['good'] += 1
            elif score >= 5:
                stats['quality_distribution']['average'] += 1
            for use_case in prompt.get('use_cases', []):
                stats['use_case_distribution'][use_case] = stats['use_case_distribution'].get(use_case, 0) + 1
        return stats
    
    def export_to_csv(self, prompts: List[Dict], output_file: Path):
        if not prompts:
            return
        fieldnames = ['id', 'title', 'prompt_text', 'prompt_zh', 'platform', 'genre', 'bpm', 'key', 'instruments', 'quality_score', 'use_cases', 'source']
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for prompt in prompts:
                row = {
                    'id': prompt.get('id', ''),
                    'title': prompt.get('title', ''),
                    'prompt_text': prompt.get('prompt_text', ''),
                    'prompt_zh': prompt.get('prompt_zh', ''),
                    'platform': prompt.get('platform', ''),
                    'genre': ', '.join(prompt.get('genre', [])),
                    'bpm': prompt.get('bpm', ''),
                    'key': prompt.get('key', ''),
                    'instruments': ', '.join(prompt.get('instruments', [])),
                    'quality_score': prompt.get('quality_score', 0),
                    'use_cases': ', '.join(prompt.get('use_cases', [])),
                    'source': prompt.get('source', '')
                }
                writer.writerow(row)
        print(f"CSV exported: {output_file}")
    
    def export_curated_csv(self, prompts: List[Dict], output_file: Path):
        curated = [p for p in prompts if p.get('quality_score', 0) >= 8]
        if not curated:
            return
        fieldnames = ['id', 'title', 'prompt_text', 'prompt_zh', 'platform', 'genre', 'bpm', 'key', 'instruments', 'quality_score', 'use_cases', 'usage_tips', 'param_tips', 'similar_styles']
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for prompt in curated:
                row = {
                    'id': prompt.get('id', ''),
                    'title': prompt.get('title', ''),
                    'prompt_text': prompt.get('prompt_text', ''),
                    'prompt_zh': prompt.get('prompt_zh', ''),
                    'platform': prompt.get('platform', ''),
                    'genre': ', '.join(prompt.get('genre', [])),
                    'bpm': prompt.get('bpm', ''),
                    'key': prompt.get('key', ''),
                    'instruments': ', '.join(prompt.get('instruments', [])),
                    'quality_score': prompt.get('quality_score', 0),
                    'use_cases': ', '.join(prompt.get('use_cases', [])),
                    'usage_tips': ' | '.join(prompt.get('usage_tips', [])),
                    'param_tips': str(prompt.get('param_tips', {})),
                    'similar_styles': ', '.join(prompt.get('similar_styles', []))
                }
                writer.writerow(row)
        print(f"Curated CSV exported: {output_file}")
    
    def update_index_json(self, stats: Dict, output_file: Path):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"Index updated: {output_file}")
    
    def run_git_commands(self, message: str, push: bool = True):
        commands = [['git', 'add', '-A'], ['git', 'commit', '-m', message]]
        if push:
            commands.append(['git', 'push'])
        for cmd in commands:
            try:
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=True)
                print(f"Executed: {' '.join(cmd)}")
                if result.stdout:
                    print(result.stdout)
            except subprocess.CalledProcessError as e:
                if 'nothing to commit' in (e.stdout or ''):
                    print("No changes to commit")
                else:
                    print(f"Git command failed: {e.stderr}")
                return False
        return True
    
    def publish(self, push: bool = True, custom_message: str = None):
        print("=" * 60)
        print("MUSICprompt Automated Publishing")
        print("=" * 60)
        print("\n[1/5] Loading prompt data...")
        prompts = self.load_all_prompts()
        print(f"  Loaded {len(prompts)} prompts")
        print("\n[2/5] Generating statistics...")
        stats = self.generate_statistics(prompts)
        print(f"  Total: {stats['total_prompts']}, Curated: {stats['curated_count']}, Translated: {stats['translated_count']}")
        print("\n[3/5] Updating index...")
        self.update_index_json(stats, self.output_dir / "index.json")
        print("\n[4/5] Exporting CSV...")
        csv_dir = self.output_dir / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        self.export_to_csv(prompts, csv_dir / "all_prompts.csv")
        self.export_curated_csv(prompts, csv_dir / "curated_prompts.csv")
        print("\n[5/5] Git commit...")
        message = custom_message or f"data: update prompt library - {datetime.now().strftime('%Y-%m-%d')}"
        success = self.run_git_commands(message, push)
        print("\n" + "=" * 60)
        print("Publish complete!" if success else "Publish complete (no changes)")
        print("=" * 60)
        return stats


def main():
    parser = argparse.ArgumentParser(description="MUSICprompt Automated Publishing Script")
    parser.add_argument('--no-push', action='store_true', help='Do not push to remote')
    parser.add_argument('--message', type=str, help='Custom commit message')
    args = parser.parse_args()
    project_root = Path(__file__).parent.parent
    manager = PublishManager(project_root)
    manager.publish(push=not args.no_push, custom_message=args.message)


if __name__ == "__main__":
    main()
