#!/usr/bin/env python3
"""
AI音乐提示词输出格式化工具
生成结构化的最终输出文件
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constants import USE_CASE_NAMES


class OutputFormatter:
    """输出格式化器"""
    
    def __init__(self, data_dir: Path = None):
        from src.config import config as app_config
        self.data_dir = data_dir or app_config.data_dir
        self.output_base = self.data_dir / "final_output"
        
    def load_translated_prompts(self) -> List[Dict]:
        """加载翻译后的提示词"""
        file_path = self.data_dir / "processed" / "extracted" / "translated_prompts.json"
        if not file_path.exists():
            file_path = self.data_dir / "processed" / "extracted" / "extracted_prompts.json"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def organize_by_genre(self, prompts: List[Dict]) -> Dict[str, List[Dict]]:
        """按流派组织提示词"""
        genre_groups = defaultdict(list)
        
        for prompt in prompts:
            genres = prompt.get('genre', [])
            if genres:
                primary_genre = genres[0]
                genre_groups[primary_genre].append(prompt)
            else:
                genre_groups['uncategorized'].append(prompt)
        
        return dict(genre_groups)
    
    def organize_by_use_case(self, prompts: List[Dict]) -> Dict[str, List[Dict]]:
        """按使用场景组织提示词"""
        use_case_groups = defaultdict(list)
        
        for prompt in prompts:
            use_cases = prompt.get('use_cases', [])
            if use_cases:
                for use_case in use_cases:
                    use_case_groups[use_case].append(prompt)
            else:
                use_case_groups['general'].append(prompt)
        
        return dict(use_case_groups)
    
    def create_genre_documents(self, genre_groups: Dict[str, List[Dict]]):
        """创建流派分类文档"""
        genres_dir = self.output_base / "genres"
        genres_dir.mkdir(parents=True, exist_ok=True)
        
        for genre, prompts in genre_groups.items():
            sorted_prompts = sorted(
                prompts,
                key=lambda x: x.get('quality_score', 0),
                reverse=True
            )
            
            md_content = self._generate_genre_markdown(genre, sorted_prompts)
            
            md_file = genres_dir / f"{genre}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            json_file = genres_dir / f"{genre}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_prompts, f, ensure_ascii=False, indent=2)
            
            print(f"  生成: {genre} ({len(prompts)} 条)")
    
    def _generate_genre_markdown(self, genre: str, prompts: List[Dict]) -> str:
        """生成流派Markdown文档"""
        from src.constants import GENRE_ICONS
        icon = GENRE_ICONS.get(genre, "\U0001f3b5")
        
        lines = [
            f"# {icon} {genre.upper()} 音乐提示词集",
            "",
            f"> 共收录 {len(prompts)} 条高质量提示词",
            "",
            "## 目录",
            "",
        ]
        
        for i, prompt in enumerate(prompts[:20], 1):
            title = prompt.get('title', f'提示词 #{i}')
            score = prompt.get('quality_score', 0)
            lines.append(f"{i}. [{title}](#prompt-{i}) - 质量分: {score}")
        
        if len(prompts) > 20:
            lines.append(f"\n... 还有 {len(prompts) - 20} 条提示词")
        
        lines.extend(["", "---", ""])
        
        for i, prompt in enumerate(prompts, 1):
            lines.extend(self._format_prompt_section(prompt, i))
        
        return '\n'.join(lines)
    
    def _format_prompt_section(self, prompt: Dict, index: int) -> List[str]:
        """格式化单条提示词部分"""
        lines = [
            f"### 提示词 #{index}",
            "",
            f"**质量评分**: {prompt.get('quality_score', 0)}/10",
            "",
            f"**平台**: {prompt.get('platform', 'Unknown')}",
            "",
        ]
        
        bpm = prompt.get('bpm')
        key = prompt.get('key')
        instruments = prompt.get('instruments', [])
        
        if bpm or key or instruments:
            lines.append("**技术参数**:")
            if bpm:
                lines.append(f"- BPM: {bpm}")
            if key:
                lines.append(f"- 调性: {key}")
            if instruments:
                lines.append(f"- 乐器: {', '.join(instruments)}")
            lines.append("")
        
        genres = prompt.get('genre', [])
        if genres:
            lines.append(f"**流派**: {', '.join(genres)}")
            lines.append("")
        
        use_cases = prompt.get('use_cases', [])
        if use_cases:
            lines.append(f"**适用场景**: {', '.join(use_cases)}")
            lines.append("")
        
        lines.extend([
            "#### 英文提示词",
            "```",
            prompt.get('prompt_text', ''),
            "```",
            "",
        ])
        
        prompt_zh = prompt.get('prompt_zh', '')
        if prompt_zh and prompt_zh != prompt.get('prompt_text', ''):
            lines.extend([
                "#### 中文翻译",
                "```",
                prompt_zh,
                "```",
                "",
            ])
        
        lines.extend(["---", ""])
        return lines
    
    def create_use_case_documents(self, use_case_groups: Dict[str, List[Dict]]):
        """创建使用场景分类文档"""
        use_cases_dir = self.output_base / "use_cases"
        use_cases_dir.mkdir(parents=True, exist_ok=True)
        
        for use_case, prompts in use_case_groups.items():
            sorted_prompts = sorted(
                prompts,
                key=lambda x: x.get('quality_score', 0),
                reverse=True
            )
            
            md_content = self._generate_use_case_markdown(use_case, sorted_prompts)
            
            md_file = use_cases_dir / f"{use_case}.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"  场景: {use_case} ({len(prompts)} 条)")
    
    def _generate_use_case_markdown(self, use_case: str, prompts: List[Dict]) -> str:
        """生成使用场景Markdown文档"""
        cn_name = USE_CASE_NAMES.get(use_case, use_case)
        
        lines = [
            f"# {cn_name} 音乐提示词集",
            "",
            f"> 共收录 {len(prompts)} 条适合{cn_name}场景的高质量提示词",
            "",
            "## 推荐提示词",
            "",
        ]
        
        for i, prompt in enumerate(prompts[:15], 1):
            lines.extend(self._format_prompt_section(prompt, i))
        
        return '\n'.join(lines)
    
    def create_master_index(self, prompts: List[Dict]):
        """创建主索引文件"""
        index = {
            'total_prompts': len(prompts),
            'quality_summary': {
                'excellent': sum(1 for p in prompts if p.get('quality_score', 0) >= 9),
                'good': sum(1 for p in prompts if 7 <= p.get('quality_score', 0) < 9),
                'average': sum(1 for p in prompts if 5 <= p.get('quality_score', 0) < 7),
            },
            'genre_summary': {},
            'platform_summary': {},
            'top_10_prompts': []
        }
        
        for prompt in prompts:
            for genre in prompt.get('genre', []):
                index['genre_summary'][genre] = \
                    index['genre_summary'].get(genre, 0) + 1
        
        for prompt in prompts:
            platform = prompt.get('platform', 'unknown')
            index['platform_summary'][platform] = \
                index['platform_summary'].get(platform, 0) + 1
        
        top_prompts = sorted(
            prompts,
            key=lambda x: x.get('quality_score', 0),
            reverse=True
        )[:10]
        
        index['top_10_prompts'] = [
            {
                'id': p.get('id'),
                'title': p.get('title', ''),
                'score': p.get('quality_score', 0),
                'genre': p.get('genre', []),
                'preview': p.get('prompt_text', '')[:80] + '...'
            }
            for p in top_prompts
        ]
        
        index_file = self.output_base / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        md_index = self._generate_master_index_markdown(index)
        md_file = self.output_base / "README.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_index)
        
        print(f"\n主索引已生成: {index_file}")
    
    def _generate_master_index_markdown(self, index: Dict) -> str:
        """生成主索引Markdown"""
        lines = [
            "# AI音乐提示词库",
            "",
            f"> 共收录 **{index['total_prompts']}** 条高质量AI音乐生成提示词",
            "",
            "## 质量分布",
            "",
            f"- 优秀 (9-10分): {index['quality_summary']['excellent']} 条",
            f"- 良好 (7-8.9分): {index['quality_summary']['good']} 条",
            f"- 一般 (5-6.9分): {index['quality_summary']['average']} 条",
            "",
            "## 流派分类",
            "",
        ]
        
        sorted_genres = sorted(
            index['genre_summary'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for genre, count in sorted_genres:
            lines.append(f"- [{genre}](genres/{genre}.md) - {count} 条")
        
        lines.extend([
            "",
            "## 使用场景",
            "",
        ])
        
        for uc_key, uc_name in USE_CASE_NAMES.items():
            lines.append(f"- [{uc_name}](use_cases/{uc_key}.md)")
        
        lines.extend([
            "",
            "## 热门提示词 Top 10",
            "",
        ])
        
        for i, prompt in enumerate(index['top_10_prompts'], 1):
            lines.append(f"{i}. **{prompt['title'] or '未命名'}** (评分: {prompt['score']})")
            lines.append(f"   - 流派: {', '.join(prompt['genre'])}")
            lines.append(f"   - {prompt['preview']}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_all(self):
        """生成所有输出文件"""
        print("=" * 60)
        print("生成最终输出文件")
        print("=" * 60)
        
        prompts = self.load_translated_prompts()
        if not prompts:
            print("错误: 没有找到提示词数据")
            return
        
        print(f"加载了 {len(prompts)} 条提示词\n")
        
        print("生成流派分类文档...")
        genre_groups = self.organize_by_genre(prompts)
        self.create_genre_documents(genre_groups)
        
        print("\n生成使用场景文档...")
        use_case_groups = self.organize_by_use_case(prompts)
        self.create_use_case_documents(use_case_groups)
        
        print("\n生成主索引...")
        self.create_master_index(prompts)
        
        print("\n" + "=" * 60)
        print(f"输出完成! 文件保存在: {self.output_base}")
        print("=" * 60)


def main():
    from src.config import config as app_config
    formatter = OutputFormatter(app_config.data_dir)
    formatter.generate_all()


if __name__ == "__main__":
    main()
