#!/usr/bin/env python3
"""
AI音乐提示词提取与质量评估工具
从真实用户数据中提取高质量提示词
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config as app_config
from src.constants import (
    TECH_KEYWORDS,
    INSTRUMENTS,
    GENRES,
    STRUCTURE_TAGS,
    SCENARIO_MAP,
)


@dataclass
class MusicPrompt:
    """音乐提示词数据模型"""
    id: str
    prompt_text: str
    prompt_zh: str = ""
    platform: str = ""  # suno / udio
    genre: List[str] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    instruments: List[str] = None
    quality_score: float = 0.0
    use_cases: List[str] = None
    source: str = ""
    title: str = ""
    
    def __post_init__(self):
        if self.genre is None:
            self.genre = []
        if self.instruments is None:
            self.instruments = []
        if self.use_cases is None:
            self.use_cases = []


class PromptQualityScorer:
    """提示词质量评分器"""

    def __init__(self):
        self.score_weights = {
            'technical_params': 0.25,
            'structure': 0.20,
            'genre_clarity': 0.20,
            'instrument_spec': 0.20,
            'length_appropriateness': 0.15
        }

    def score(self, prompt_text: str) -> float:
        """计算提示词质量分数 (0-10)"""
        text_lower = prompt_text.lower()
        scores = {}

        tech_count = sum(1 for kw in TECH_KEYWORDS if kw in text_lower)
        scores['technical_params'] = min(tech_count / 3, 1.0) * 10

        structure_count = sum(1 for tag in STRUCTURE_TAGS if tag in text_lower)
        scores['structure'] = min(structure_count / 2, 1.0) * 10

        genre_count = sum(1 for g in GENRES if g in text_lower)
        scores['genre_clarity'] = min(genre_count / 2, 1.0) * 10

        instrument_count = sum(1 for inst in INSTRUMENTS if inst in text_lower)
        scores['instrument_spec'] = min(instrument_count / 2, 1.0) * 10

        length = len(prompt_text)
        if 50 <= length <= 950:
            scores['length_appropriateness'] = 10
        elif length < 50:
            scores['length_appropriateness'] = length / 50 * 10
        else:
            scores['length_appropriateness'] = max(0, 10 - (length - 950) / 100)

        total_score = sum(
            scores[key] * self.score_weights[key]
            for key in scores
        )

        return round(total_score, 2)

    def extract_technical_params(self, text: str) -> Dict[str, Any]:
        """提取技术参数"""
        params = {}
        text_lower = text.lower()

        bpm_match = re.search(r'(?:bpm|tempo)[:\s]*(\d+)', text_lower)
        if bpm_match:
            bpm = int(bpm_match.group(1))
            if 40 <= bpm <= 250:
                params['bpm'] = bpm

        key_match = re.search(r'(?:key|scale)[:\s]*([a-g][#\s]?\s*(?:major|minor))', text_lower)
        if key_match:
            params['key'] = key_match.group(1).strip()

        instruments = []
        for inst in INSTRUMENTS:
            if inst in text_lower:
                instruments.append(inst)
        if instruments:
            params['instruments'] = instruments[:5]

        return params

    def extract_genres(self, text: str) -> List[str]:
        """提取流派标签"""
        text_lower = text.lower()
        genres = []
        for genre in GENRES:
            if genre in text_lower:
                genres.append(genre)
        return genres[:3]

    def determine_use_cases(self, text: str) -> List[str]:
        """确定使用场景"""
        text_lower = text.lower()
        use_cases = []

        for scenario, keywords in SCENARIO_MAP.items():
            if any(kw in text_lower for kw in keywords):
                use_cases.append(scenario)

        return use_cases[:3]


class PromptExtractor:
    """提示词提取器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.scorer = PromptQualityScorer()
        self.extracted_prompts: List[MusicPrompt] = []
        
    def load_json_data(self, file_path: Path) -> List[List]:
        """加载JSON数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # mister-magpie 数据格式: {"data": [{"customdata": [[...], [...]]}]}
                if 'data' in data and len(data['data']) > 0:
                    first_item = data['data'][0]
                    if 'customdata' in first_item:
                        return first_item['customdata']
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return []
    
    def extract_from_magpie_data(self, records: List[List]) -> List[MusicPrompt]:
        """从mister-magpie数据格式提取提示词"""
        prompts = []
        
        for record in records:
            if not isinstance(record, list) or len(record) < 6:
                continue
            
            # mister-magpie格式: [id, platform, title, cluster, cluster_name, prompt_text]
            try:
                song_id = record[0]
                platform = record[1]
                title = record[2]
                prompt_text = record[5] if len(record) > 5 else ""
                
                # 过滤无效提示词
                if not self._is_valid_prompt(prompt_text):
                    continue
                
                # 计算质量分数
                quality_score = self.scorer.score(prompt_text)
                
                # 只保留高质量提示词 (>= 5.0)
                if quality_score < 5.0:
                    continue
                
                # 提取技术参数
                tech_params = self.scorer.extract_technical_params(prompt_text)
                
                # 提取流派
                genres = self.scorer.extract_genres(prompt_text)
                
                # 确定使用场景
                use_cases = self.scorer.determine_use_cases(prompt_text)
                
                # 生成唯一ID
                content_hash = hashlib.md5(prompt_text.encode()).hexdigest()[:12]
                
                prompt = MusicPrompt(
                    id=f"mp_{content_hash}",
                    prompt_text=prompt_text,
                    prompt_zh="",  # 待翻译
                    platform=platform,
                    genre=genres,
                    bpm=tech_params.get('bpm'),
                    key=tech_params.get('key'),
                    instruments=tech_params.get('instruments', []),
                    quality_score=quality_score,
                    use_cases=use_cases,
                    source=f"mister-magpie/{song_id}",
                    title=title
                )
                
                prompts.append(prompt)
                
            except Exception as e:
                continue
        
        return prompts
    
    def _is_valid_prompt(self, text: str) -> bool:
        """检查提示词是否有效"""
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        
        # 过滤条件
        if len(text) < 20:  # 太短
            return False
        if len(text) > 2000:  # 太长
            return False
        
        # 过滤纯歌词（没有风格描述）
        lines = text.split('\n')
        if len(lines) > 5 and '[' not in text:
            # 可能是纯歌词
            return False
        
        # 过滤元数据描述
        metadata_patterns = [
            r'^\d+\s+prompts',
            r'^awesome.*prompts',
            r'^github\.com',
            r'^http',
        ]
        for pattern in metadata_patterns:
            if re.search(pattern, text.lower()):
                return False
        
        return True
    
    def process_all_sources(self):
        """处理所有数据源"""
        # 处理mister-magpie数据
        magpie_file = self.data_dir / "external" / "mister-magpie_aims_prompts" / "plots" / "prompt_hdb_names.json"
        if magpie_file.exists():
            print(f"处理: {magpie_file}")
            records = self.load_json_data(magpie_file)
            prompts = self.extract_from_magpie_data(records)
            self.extracted_prompts.extend(prompts)
            print(f"  提取了 {len(prompts)} 条高质量提示词")
        
        # 去重
        seen_ids = set()
        unique_prompts = []
        for p in self.extracted_prompts:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_prompts.append(p)
        
        self.extracted_prompts = unique_prompts
        print(f"\n总计: {len(self.extracted_prompts)} 条唯一提示词")
        
        # 统计质量分布
        scores = [p.quality_score for p in self.extracted_prompts]
        if scores:
            print(f"质量分数分布:")
            print(f"  平均: {sum(scores)/len(scores):.2f}")
            print(f"  最高: {max(scores):.2f}")
            print(f"  最低: {min(scores):.2f}")
            print(f"  8分以上: {sum(1 for s in scores if s >= 8)}/{len(scores)}")
    
    def save_extracted(self, output_dir: Path):
        """保存提取的提示词"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 按质量分数排序
        sorted_prompts = sorted(
            self.extracted_prompts,
            key=lambda x: x.quality_score,
            reverse=True
        )
        
        # 保存为JSON
        output_file = output_dir / "extracted_prompts.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(p) for p in sorted_prompts],
                f,
                ensure_ascii=False,
                indent=2
            )
        
        print(f"\n已保存到: {output_file}")
        
        # 生成统计报告
        self._generate_report(output_dir)
    
    def _generate_report(self, output_dir: Path):
        """生成统计报告"""
        report = {
            'total_extracted': len(self.extracted_prompts),
            'quality_distribution': {
                'excellent (9-10)': sum(1 for p in self.extracted_prompts if p.quality_score >= 9),
                'good (7-8.9)': sum(1 for p in self.extracted_prompts if 7 <= p.quality_score < 9),
                'average (5-6.9)': sum(1 for p in self.extracted_prompts if 5 <= p.quality_score < 7),
            },
            'platform_distribution': {},
            'genre_distribution': {},
            'top_prompts': []
        }
        
        # 平台分布
        for p in self.extracted_prompts:
            report['platform_distribution'][p.platform] = \
                report['platform_distribution'].get(p.platform, 0) + 1
        
        # 流派分布
        for p in self.extracted_prompts:
            for g in p.genre:
                report['genre_distribution'][g] = \
                    report['genre_distribution'].get(g, 0) + 1
        
        # 前10条最高质量提示词
        top_prompts = sorted(
            self.extracted_prompts,
            key=lambda x: x.quality_score,
            reverse=True
        )[:10]
        
        report['top_prompts'] = [
            {
                'id': p.id,
                'score': p.quality_score,
                'genre': p.genre,
                'preview': p.prompt_text[:100] + '...' if len(p.prompt_text) > 100 else p.prompt_text
            }
            for p in top_prompts
        ]
        
        # 保存报告
        report_file = output_dir / "extraction_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"报告已保存: {report_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("AI音乐提示词提取工具")
    print("=" * 60)
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = data_dir / "processed" / "extracted"
    
    # 创建提取器
    extractor = PromptExtractor(data_dir)
    
    # 处理所有数据源
    extractor.process_all_sources()
    
    # 保存结果
    extractor.save_extracted(output_dir)
    
    print("\n" + "=" * 60)
    print("提取完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
