#!/usr/bin/env python3
"""
AI音乐提示词翻译工具
使用SiliconFlow API进行专业音乐术语翻译
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import asdict
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()


class MusicTermGlossary:
    """音乐术语词典"""
    
    # 技术术语 - 保留英文
    TECH_TERMS = {
        'bpm': 'BPM',
        'tempo': 'Tempo',
        'key': '调性',
        'major': '大调',
        'minor': '小调',
        'scale': '音阶',
        'reverb': '混响 (Reverb)',
        'compression': '压缩 (Compression)',
        'saturation': '饱和 (Saturation)',
        'eq': '均衡 (EQ)',
        'sidechain': '侧链 (Sidechain)',
        'distortion': '失真 (Distortion)',
        'delay': '延迟 (Delay)',
        'chorus': '合唱效果 (Chorus)',
        'flanger': '镶边 (Flanger)',
        'phaser': '相位 (Phaser)',
    }
    
    # 乐器名称
    INSTRUMENTS = {
        'guitar': '吉他 (Guitar)',
        'electric guitar': '电吉他 (Electric Guitar)',
        'acoustic guitar': '原声吉他 (Acoustic Guitar)',
        'bass': '贝斯 (Bass)',
        'bass guitar': '贝斯吉他 (Bass Guitar)',
        'drums': '鼓组 (Drums)',
        'piano': '钢琴 (Piano)',
        'synth': '合成器 (Synth)',
        'synthesizer': '合成器 (Synthesizer)',
        'violin': '小提琴 (Violin)',
        'cello': '大提琴 (Cello)',
        'flute': '长笛 (Flute)',
        'saxophone': '萨克斯 (Saxophone)',
        'trumpet': '小号 (Trumpet)',
        'harp': '竖琴 (Harp)',
        'ukulele': '尤克里里 (Ukulele)',
        'keyboard': '键盘 (Keyboard)',
        'hurdy-gurdy': '手摇风琴 (Hurdy-Gurdy)',
        'mandolin': '曼陀林 (Mandolin)',
        'banjo': '班卓琴 (Banjo)',
    }
    
    # 流派名称
    GENRES = {
        'rock': '摇滚 (Rock)',
        'pop': '流行 (Pop)',
        'hip hop': '嘻哈 (Hip Hop)',
        'rap': '说唱 (Rap)',
        'electronic': '电子 (Electronic)',
        'edm': '电子舞曲 (EDM)',
        'jazz': '爵士 (Jazz)',
        'blues': '布鲁斯 (Blues)',
        'classical': '古典 (Classical)',
        'folk': '民谣 (Folk)',
        'country': '乡村 (Country)',
        'r&b': '节奏布鲁斯 (R&B)',
        'soul': '灵魂乐 (Soul)',
        'funk': '放克 (Funk)',
        'metal': '金属 (Metal)',
        'punk': '朋克 (Punk)',
        'indie': '独立 (Indie)',
        'ambient': '氛围 (Ambient)',
        'lo-fi': '低保真 (Lo-Fi)',
        'trap': '陷阱 (Trap)',
        'house': '浩室 (House)',
        'techno': '铁克诺 (Techno)',
        'trance': '迷幻舞曲 (Trance)',
        'dubstep': '回响贝斯 (Dubstep)',
        'synthwave': '合成器波 (Synthwave)',
    }
    
    # 情绪/风格修饰词
    MOOD_MODIFIERS = {
        'melancholy': '忧郁的',
        'ethereal': '空灵飘渺的',
        'haunting': '萦绕心头的',
        'dreamy': '梦幻的',
        'dark': '黑暗的',
        'bright': '明亮的',
        'warm': '温暖的',
        'cold': '冷峻的',
        'raw': '原始的',
        'polished': '精致的',
        'gritty': '粗犷的',
        'smooth': '顺滑的',
        'aggressive': '激进的',
        'gentle': '温柔的',
        'powerful': '有力的',
        'intimate': '亲密的',
        'epic': '史诗的',
        'nostalgic': '怀旧的',
        'futuristic': '未来感的',
        'vintage': '复古的',
        'analog': '模拟的',
        'digital': '数字的',
        'lo-fi': '低保真的',
        'hi-fi': '高保真的',
    }
    
    # 结构标签
    STRUCTURE_TAGS = {
        '[intro]': '[前奏 Intro]',
        '[verse]': '[主歌 Verse]',
        '[chorus]': '[副歌 Chorus]',
        '[bridge]': '[桥段 Bridge]',
        '[outro]': '[尾奏 Outro]',
        '[hook]': '[钩子 Hook]',
        '[pre-chorus]': '[导歌 Pre-Chorus]',
        '[interlude]': '[间奏 Interlude]',
        '[break]': '[中断 Break]',
        '[solo]': '[独奏 Solo]',
        '[build]': '[ buildup Build]',
        '[drop]': '[ drop Drop]',
    }
    
    @classmethod
    def translate_structure_tags(cls, text: str) -> str:
        """翻译结构标签"""
        for en_tag, zh_tag in cls.STRUCTURE_TAGS.items():
            text = text.replace(en_tag, zh_tag)
            text = text.replace(en_tag.replace('[', '[').replace(']', ']'), zh_tag)
        return text


class PromptTranslator:
    """提示词翻译器"""
    
    def __init__(self):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("未设置 SILICONFLOW_API_KEY 环境变量")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        self.model = "Qwen/Qwen2.5-72B-Instruct"
        self.request_count = 0
        self.last_request_time = 0
        self.min_interval = 0.5  # 免费版限速
        
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def translate_prompt(self, prompt_text: str) -> Dict[str, str]:
        """翻译单个提示词"""
        self._rate_limit()
        
        system_prompt = """你是一位专业的音乐制作人和翻译专家。请将以下AI音乐生成提示词翻译成中文。

翻译要求：
1. 保留所有技术参数（BPM、调性、乐器名称等）的英文原文
2. 音乐流派名称采用"中文译名 (English)"的格式
3. 情绪修饰词使用中文音乐行业常用表达
4. 结构标签如[Verse]、[Chorus]等翻译为[主歌]、[副歌]等
5. 保持原有的标点符号和格式结构
6. 确保翻译后的提示词可以直接用于中文用户理解

请返回JSON格式：
{
    "title_zh": "中文标题",
    "prompt_zh": "完整的中文翻译提示词",
    "genre_tags": ["流派标签1", "流派标签2"],
    "mood_keywords": ["情绪关键词1", "情绪关键词2"]
}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请翻译以下音乐提示词：\n\n{prompt_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            self.request_count += 1
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"翻译失败: {e}")
            return {
                "title_zh": "",
                "prompt_zh": "",
                "genre_tags": [],
                "mood_keywords": []
            }
    
    def batch_translate(self, prompts: List[Dict], batch_size: int = 10) -> List[Dict]:
        """批量翻译提示词"""
        translated = []
        total = len(prompts)
        
        print(f"开始批量翻译，共 {total} 条提示词...")
        print(f"预计耗时: {total * 0.5 / 60:.1f} 分钟\n")
        
        for i, prompt in enumerate(prompts):
            if i % 10 == 0:
                print(f"[{i+1}/{total}] 翻译中...")
            
            # 翻译
            translation = self.translate_prompt(prompt['prompt_text'])
            
            # 更新提示词数据
            prompt['prompt_zh'] = translation.get('prompt_zh', '')
            if not prompt['prompt_zh']:
                # 如果翻译失败，保留原文
                prompt['prompt_zh'] = prompt['prompt_text']
            
            # 添加翻译元数据
            prompt['translation_meta'] = {
                'title_zh': translation.get('title_zh', ''),
                'genre_tags_zh': translation.get('genre_tags', []),
                'mood_keywords_zh': translation.get('mood_keywords', []),
                'translated_at': datetime.now().isoformat()
            }
            
            translated.append(prompt)
        
        print(f"\n翻译完成! 共处理 {len(translated)} 条提示词")
        return translated


def main():
    """主函数"""
    print("=" * 60)
    print("AI音乐提示词翻译工具")
    print("=" * 60)
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "extracted" / "extracted_prompts.json"
    output_file = project_root / "data" / "processed" / "extracted" / "translated_prompts.json"
    
    if not input_file.exists():
        print(f"错误: 找不到输入文件 {input_file}")
        print("请先运行 prompt_extractor.py 提取提示词")
        return
    
    # 加载提取的提示词
    print(f"加载提示词: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    print(f"共加载 {len(prompts)} 条提示词")
    
    # 只翻译高质量的提示词（分数>=7）
    high_quality = [p for p in prompts if p.get('quality_score', 0) >= 7]
    print(f"高质量提示词 (>=7分): {len(high_quality)} 条")
    
    # 创建翻译器
    translator = PromptTranslator()
    
    # 批量翻译
    translated = translator.batch_translate(high_quality)
    
    # 保存结果
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)
    
    print(f"\n已保存到: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
