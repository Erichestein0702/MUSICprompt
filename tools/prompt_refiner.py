#!/usr/bin/env python3
"""
AI音乐提示词精校工具
对8分以上的顶级提示词进行人工级优化
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class PromptRefiner:
    """提示词精校器"""
    
    def __init__(self):
        self.refined_count = 0
    
    def load_prompts(self, file_path: Path) -> List[Dict]:
        """加载提示词"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def refine_prompt(self, prompt: Dict) -> Dict:
        """精校单条提示词"""
        # 提取关键信息
        prompt_text = prompt.get('prompt_text', '')
        prompt_zh = prompt.get('prompt_zh', '')
        
        # 优化1: 添加使用建议
        usage_tips = self._generate_usage_tips(prompt)
        prompt['usage_tips'] = usage_tips
        
        # 优化2: 添加参数调整建议
        param_tips = self._generate_param_tips(prompt)
        prompt['param_tips'] = param_tips
        
        # 优化3: 添加类似风格推荐
        similar_styles = self._generate_similar_styles(prompt)
        prompt['similar_styles'] = similar_styles
        
        # 优化4: 标记为精校版本
        prompt['refined'] = True
        prompt['refined_version'] = '1.0'
        
        self.refined_count += 1
        return prompt
    
    def _generate_usage_tips(self, prompt: Dict) -> List[str]:
        """生成使用建议"""
        tips = []
        genre = prompt.get('genre', [])
        use_cases = prompt.get('use_cases', [])
        bpm = prompt.get('bpm')
        
        # 基于流派的建议
        if 'rock' in genre:
            tips.append("适合作为背景音乐，建议调整吉他音色来匹配情绪")
        if 'electronic' in genre:
            tips.append("可以尝试调整BPM来改变能量感")
        if 'ambient' in genre:
            tips.append("适合冥想或学习场景，建议保持原参数")
        
        # 基于BPM的建议
        if bpm:
            if bpm < 80:
                tips.append("慢速节奏，适合放松或情感表达")
            elif bpm > 120:
                tips.append("快速节奏，适合运动或派对场景")
        
        # 基于场景的建议
        if 'workout' in use_cases:
            tips.append("健身时使用建议调高音量，增强动力")
        if 'study' in use_cases:
            tips.append("学习时使用建议降低音量，避免分心")
        
        return tips[:3]  # 最多3条建议
    
    def _generate_param_tips(self, prompt: Dict) -> Dict[str, str]:
        """生成参数调整建议"""
        tips = {}
        bpm = prompt.get('bpm')
        key = prompt.get('key')
        
        if bpm:
            tips['bpm'] = f"当前BPM: {bpm}，可尝试 ±10 调整来改变速度感"
        
        if key:
            tips['key'] = f"当前调性: {key}，小调更忧郁，大调更明亮"
        
        tips['instruments'] = "可以尝试替换主要乐器来改变风格，如将吉他换成钢琴"
        
        return tips
    
    def _generate_similar_styles(self, prompt: Dict) -> List[str]:
        """生成类似风格推荐"""
        genre = prompt.get('genre', [])
        similar = []
        
        style_mappings = {
            'rock': ['hard rock', 'indie rock', 'alternative rock'],
            'electronic': ['synthwave', 'ambient electronic', 'future bass'],
            'pop': ['synth pop', 'indie pop', 'electropop'],
            'hip hop': ['trap', 'lo-fi hip hop', 'boom bap'],
            'jazz': ['smooth jazz', 'fusion', 'bebop'],
            'classical': ['orchestral', 'chamber music', 'piano solo'],
        }
        
        for g in genre:
            if g in style_mappings:
                similar.extend(style_mappings[g])
        
        return similar[:3]
    
    def refine_batch(self, prompts: List[Dict], min_score: float = 8.0) -> List[Dict]:
        """批量精校提示词"""
        # 筛选高分提示词
        high_quality = [p for p in prompts if p.get('quality_score', 0) >= min_score]
        
        print(f"开始精校 {len(high_quality)} 条高分提示词 (>= {min_score}分)...")
        
        refined = []
        for i, prompt in enumerate(high_quality, 1):
            if i % 10 == 0:
                print(f"  已处理 {i}/{len(high_quality)}")
            refined_prompt = self.refine_prompt(prompt)
            refined.append(refined_prompt)
        
        print(f"精校完成! 共优化 {self.refined_count} 条提示词")
        return refined
    
    def create_curated_collection(self, refined_prompts: List[Dict], output_dir: Path):
        """创建精校合集"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 按流派分组
        genre_groups = {}
        for prompt in refined_prompts:
            genres = prompt.get('genre', ['uncategorized'])
            primary_genre = genres[0]
            if primary_genre not in genre_groups:
                genre_groups[primary_genre] = []
            genre_groups[primary_genre].append(prompt)
        
        # 生成精校文档
        for genre, prompts in genre_groups.items():
            # 按分数排序
            sorted_prompts = sorted(prompts, key=lambda x: x.get('quality_score', 0), reverse=True)
            
            # 生成Markdown
            md_content = self._generate_curated_markdown(genre, sorted_prompts)
            md_file = output_dir / f"{genre}_curated.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # 保存JSON
            json_file = output_dir / f"{genre}_curated.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_prompts, f, ensure_ascii=False, indent=2)
            
            print(f"  生成精校合集: {genre} ({len(prompts)} 条)")
        
        # 生成总结合集
        self._create_master_collection(refined_prompts, output_dir)
    
    def _generate_curated_markdown(self, genre: str, prompts: List[Dict]) -> str:
        """生成精校Markdown文档"""
        lines = [
            f"# {genre.upper()} 精校提示词集",
            "",
            f"> 精选 {len(prompts)} 条高质量提示词（8分以上）",
            "> 经过人工级优化，包含使用建议、参数调整指南和风格推荐",
            "",
            "## 精选提示词",
            "",
        ]
        
        for i, prompt in enumerate(prompts, 1):
            lines.extend(self._format_curated_prompt(prompt, i))
        
        return '\n'.join(lines)
    
    def _format_curated_prompt(self, prompt: Dict, index: int) -> List[str]:
        """格式化精校提示词"""
        lines = [
            f"### #{index} {prompt.get('title', '未命名')}",
            "",
            f"**质量评分**: ⭐ {prompt.get('quality_score', 0)}/10",
            f"**平台**: {prompt.get('platform', 'Unknown')}",
            "",
        ]
        
        # 技术参数
        bpm = prompt.get('bpm')
        key = prompt.get('key')
        instruments = prompt.get('instruments', [])
        
        if bpm or key or instruments:
            lines.append("**技术参数**:")
            if bpm:
                lines.append(f"- 🎵 BPM: {bpm}")
            if key:
                lines.append(f"- 🎹 调性: {key}")
            if instruments:
                lines.append(f"- 🎸 乐器: {', '.join(instruments)}")
            lines.append("")
        
        # 流派和场景
        genres = prompt.get('genre', [])
        use_cases = prompt.get('use_cases', [])
        if genres:
            lines.append(f"**流派**: {', '.join(genres)}")
        if use_cases:
            lines.append(f"**适用场景**: {', '.join(use_cases)}")
        lines.append("")
        
        # 英文原文
        lines.extend([
            "#### 📝 英文提示词",
            "```",
            prompt.get('prompt_text', ''),
            "```",
            "",
        ])
        
        # 中文翻译
        prompt_zh = prompt.get('prompt_zh', '')
        if prompt_zh and prompt_zh != prompt.get('prompt_text', ''):
            lines.extend([
                "#### 🈯 中文翻译",
                "```",
                prompt_zh,
                "```",
                "",
            ])
        
        # 使用建议
        usage_tips = prompt.get('usage_tips', [])
        if usage_tips:
            lines.extend([
                "#### 💡 使用建议",
                "",
            ])
            for tip in usage_tips:
                lines.append(f"- {tip}")
            lines.append("")
        
        # 参数调整建议
        param_tips = prompt.get('param_tips', {})
        if param_tips:
            lines.extend([
                "#### ⚙️ 参数调整指南",
                "",
            ])
            for param, tip in param_tips.items():
                lines.append(f"- **{param}**: {tip}")
            lines.append("")
        
        # 类似风格推荐
        similar_styles = prompt.get('similar_styles', [])
        if similar_styles:
            lines.extend([
                "#### 🎨 类似风格推荐",
                f"想尝试变化？可以试试: {', '.join(similar_styles)}",
                "",
            ])
        
        lines.extend(["---", ""])
        return lines
    
    def _create_master_collection(self, prompts: List[Dict], output_dir: Path):
        """创建总结合集"""
        # 按分数排序
        sorted_prompts = sorted(prompts, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # 生成README
        lines = [
            "# 🌟 AI音乐提示词精校合集",
            "",
            f"> 精选 **{len(prompts)}** 条8分以上的顶级提示词",
            "> 每条都经过优化，包含详细的使用指南",
            "",
            "## 📊 合集统计",
            "",
        ]
        
        # 流派分布
        genre_counts = {}
        for p in prompts:
            for g in p.get('genre', ['uncategorized']):
                genre_counts[g] = genre_counts.get(g, 0) + 1
        
        lines.append("### 流派分布")
        for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- [{genre}]({genre}_curated.md) - {count} 条")
        
        lines.extend([
            "",
            "## 🏆 Top 10 推荐",
            "",
        ])
        
        for i, p in enumerate(sorted_prompts[:10], 1):
            lines.append(f"{i}. **{p.get('title', '未命名')}** - {p.get('quality_score', 0)}分")
            lines.append(f"   - 流派: {', '.join(p.get('genre', []))}")
            preview = p.get('prompt_text', '')[:60]
            lines.append(f"   - {preview}...")
            lines.append("")
        
        # 保存
        readme_file = output_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        # 保存完整JSON
        json_file = output_dir / "all_curated.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_prompts, f, ensure_ascii=False, indent=2)
        
        print(f"\n总结合集已生成: {readme_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("AI音乐提示词精校工具")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "extracted" / "translated_prompts.json"
    output_dir = project_root / "data" / "final_output" / "curated"
    
    if not input_file.exists():
        print(f"错误: 找不到输入文件 {input_file}")
        return
    
    # 加载数据
    print(f"加载提示词: {input_file}")
    refiner = PromptRefiner()
    prompts = refiner.load_prompts(input_file)
    print(f"共加载 {len(prompts)} 条提示词")
    
    # 精校8分以上的提示词
    refined = refiner.refine_batch(prompts, min_score=8.0)
    
    # 创建精校合集
    print("\n生成精校合集...")
    refiner.create_curated_collection(refined, output_dir)
    
    print("\n" + "=" * 60)
    print(f"精校完成! 共优化 {len(refined)} 条顶级提示词")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
