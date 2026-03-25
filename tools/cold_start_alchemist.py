#!/usr/bin/env python
"""
MUSICprompt 冷启动炼金脚本 - 全量 Prompt 协议化处理

该脚本读取原始英文 Prompt 文件，批量调用 Gemini API 进行翻译和协议化处理，
并按流派自动分类存储到 data/genres/ 目录。

Usage:
    python tools/cold_start_alchemist.py [--input INPUT_FILE] [--batch-size SIZE]
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env 文件（不使用 python-dotenv，使用标准库实现）
def _load_env_file():
    """手动加载 .env 文件"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')  # 去除引号
                    if key and key not in os.environ:
                        os.environ[key] = value
        logging.getLogger("ColdStartAlchemist").debug(f"已加载环境变量: {env_path}")

_load_env_file()

from src.core import (
    setup_secure_logging,
    GeminiProvider,
    SiliconFlowProvider,
    ProviderFactory,
    CircuitBreaker,
    CircuitBreakerRegistry,
    ModelConfig,
    PromptContent,
    ProcessingResult,
    BatchProcessingResult,
)
from src.models import (
    MusicPromptDocument,
    MusicPromptDocumentCollection,
    DSPParameters,
    BilingualText,
    MusicGenre,
    EnergyLevel,
    SourceInfo,
    GenreStats,
)


ALCHEMIST_SYSTEM_PROMPT = """你是一位顶级音频工程师和音乐制作人，拥有 20 年的行业经验。你的任务是将英文音乐 Prompt 转换为标准化的 MUSICprompt 格式，并提供专业级的 DSP 建议。

## 处理流程

1. **翻译**：将英文 Prompt 翻译为中文，保持专业术语的准确性（如 "sidechain compression" -> "侧链压缩"）

2. **流派分类**：根据 Prompt 内容判断音乐流派，使用层级分类格式（父类.子类.孙类）：

   **电子音乐 (electronic)**：
   - electronic.bass.trap - EDM Trap（陷阱电子）
   - electronic.bass.dubstep - Dubstep（回响贝斯）
   - electronic.bass.hardstyle - Hardstyle（硬核）
   - electronic.bass - Bass 音乐（通用）
   - electronic.house - House（浩室）
   - electronic.trance - Trance（恍惚）
   - electronic.phonk_funk - Phonk & Funk（漂移放克）
   - electronic.techno - Techno（科技舞曲）
   - electronic.else - 其他电子（Electro, DnB 等）
   - electronic - 电子音乐（通用）
   
   **嘻哈 (hip_hop)**：
   - hip_hop.trap - Trap（陷阱说唱）
   - hip_hop.boombap - Boom Bap（经典嘻哈）
   - hip_hop - 嘻哈（通用）
   
   **其他主类**：
   - cinematic - 电影配乐
   - pop - 流行
   - rock - 摇滚
   - ambient - 氛围音乐
   - classical - 古典
   - jazz - 爵士
   - rnb - R&B
   - lo_fi - 低保真
   - folk - 民谣
   - world - 世界音乐
   - experimental - 实验音乐
   - other - 其他

3. **DSP 参数推断**：根据 Prompt 内容推断合理的音频参数：
   - BPM：节拍速度（40-220）
   - Key：调性（如 C Major, A Minor）
   - Energy Level：能量等级（low/medium/high/very_high）
   - Frequency Center：频率中心
   - Dynamics Range：动态范围
   - Reverb：混响类型
   - Compression：压缩风格

4. **硬核 DSP 建议**：作为顶级工程师，给出具体、可操作的混音建议，例如：
   - "Boost sub-bass at 50Hz by 3dB for deeper low end"
   - "Apply aggressive sidechain compression on pads, release at 1/8 note"
   - "Cut 200-400Hz on kick to avoid mud, boost 2-4kHz for click"
   - "Use parallel compression on drums, 4:1 ratio, slow attack"
   - "Add tape saturation on master bus, 15% drive"

5. **抖音标签生成**：生成 3-5 个适合抖音平台的中文标签

## 输出格式

必须输出严格的 JSON 格式：

```json
{
    "title_zh": "中文标题翻译",
    "prompt_zh": "中文 Prompt 完整翻译",
    "genre": "electronic.bass.dubstep",
    "douyin_tags": ["电子", "氛围感", "治愈"],
    "dsp_params": {
        "bpm": 140,
        "key": "F Minor",
        "energy_level": "very_high",
        "frequency_center": "50Hz-10kHz",
        "dynamics_range": "Wide (45dB)",
        "reverb": "Large Hall",
        "compression": "Aggressive"
    },
    "gem_suggestion": "建议在 50Hz 处提升 3dB 增强低频下潜感，对 Pad 应用侧链压缩，释放时间设为 1/8 音符。在底鼓上切除 200-400Hz 避免浑浊，提升 2-4kHz 增加打击感。"
}
```

请确保输出是有效的 JSON，不要包含任何额外的文本或注释。"""


BATCH_SIZE = 20
DEFAULT_INPUT_FILE = "data/raw/raw_prompts.txt"
GENRES_DIR = PROJECT_ROOT / "data" / "genres"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class ColdStartAlchemist:
    """
    冷启动炼金师 - 批量处理原始 Prompt
    
    负责读取原始 Prompt 文件，批量调用 AI API 进行处理，
    并按流派自动分类存储结果。
    
    支持 Provider:
    - gemini: Google Gemini (5秒/次)
    - siliconflow: SiliconFlow Qwen (0.5秒/次, 极速模式)
    """
    
    def __init__(
        self,
        input_file: str = DEFAULT_INPUT_FILE,
        batch_size: int = BATCH_SIZE,
        api_key: Optional[str] = None,
        dry_run: bool = False,
        provider: str = "gemini"
    ):
        """
        初始化炼金师
        
        Args:
            input_file: 输入文件路径
            batch_size: 批处理大小
            api_key: API Key (根据 provider 自动选择环境变量)
            dry_run: 是否为试运行模式
            provider: AI 提供者 (gemini/siliconflow)
        """
        self.input_file = Path(input_file)
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.provider_name = provider
        
        self.logger = logging.getLogger("ColdStartAlchemist")
        self.provider = None
        
        self.processed_ids: Set[str] = set()
        self.failed_prompts: List[str] = []
        self.genre_counts: Dict[MusicGenre, int] = {}
        
        self._load_processed_ids()
    
    def _load_processed_ids(self) -> None:
        """加载已处理的 Prompt ID，避免重复处理"""
        processed_file = PROCESSED_DIR / "processed_ids.json"
        if processed_file.exists():
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    self.processed_ids = set(json.load(f))
                self.logger.info(f"已加载 {len(self.processed_ids)} 个已处理 ID")
            except Exception as e:
                self.logger.warning(f"加载已处理 ID 失败: {e}")
    
    def _save_processed_ids(self) -> None:
        """保存已处理的 Prompt ID"""
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        processed_file = PROCESSED_DIR / "processed_ids.json"
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.processed_ids), f, ensure_ascii=False, indent=2)
    
    def initialize_provider(self, api_key: Optional[str] = None) -> None:
        """
        初始化 AI 提供者
        
        Args:
            api_key: API Key，如未提供则从环境变量获取
        """
        if self.dry_run:
            self.logger.info("试运行模式，跳过提供者初始化")
            return
        
        if self.provider_name == "siliconflow":
            self._init_siliconflow_provider(api_key)
        else:
            self._init_gemini_provider(api_key)
    
    def _init_gemini_provider(self, api_key: Optional[str] = None) -> None:
        """初始化 Gemini 提供者"""
        final_api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not final_api_key:
            raise ValueError(
                "未提供 Gemini API Key。请通过以下方式之一提供:\n"
                "1. 设置 GEMINI_API_KEY 环境变量\n"
                "2. 创建 .env 文件并添加 GEMINI_API_KEY=your_key\n"
                "3. 使用 --api-key 参数传入"
            )
        
        masked_key = final_api_key[:8] + "..." if len(final_api_key) > 8 else "***"
        self.logger.info(f"使用 Gemini API Key: {masked_key}")
        
        model_config = ModelConfig(
            model_name="gemini-2.5-flash-preview-05-20",
            max_tokens=4096,
            temperature=0.7,
            top_p=0.95,
            timeout=120.0
        )
        
        self.provider = GeminiProvider(
            api_key=final_api_key,
            model_config=model_config
        )
        
        self.provider.initialize()
        self.logger.info("Gemini 提供者初始化成功")
    
    def _init_siliconflow_provider(self, api_key: Optional[str] = None) -> None:
        """初始化 SiliconFlow 提供者 (极速模式)"""
        final_api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        
        if not final_api_key:
            raise ValueError(
                "未提供 SiliconFlow API Key。请通过以下方式之一提供:\n"
                "1. 设置 SILICONFLOW_API_KEY 环境变量\n"
                "2. 创建 .env 文件并添加 SILICONFLOW_API_KEY=your_key\n"
                "3. 使用 --api-key 参数传入"
            )
        
        masked_key = final_api_key[:8] + "..." if len(final_api_key) > 8 else "***"
        self.logger.info(f"使用 SiliconFlow API Key: {masked_key}")
        
        model_config = ModelConfig(
            model_name="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=4096,
            temperature=0.3,
            top_p=0.95,
            timeout=60.0
        )
        
        self.provider = SiliconFlowProvider(
            api_key=final_api_key,
            model_config=model_config
        )
        
        self.provider.initialize()
        self.logger.info("SiliconFlow 提供者初始化成功 (极速模式: 0.5秒/次)")
    
    def read_prompts(self) -> List[PromptContent]:
        """
        读取原始 Prompt 文件
        
        Returns:
            PromptContent 列表
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.input_file}")
        
        prompts = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('#') or line.startswith('//'):
                    continue
                
                parts = line.split('|||')
                prompt_text = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else None
                tags = parts[2].split(',') if len(parts) > 2 else []
                tags = [t.strip() for t in tags if t.strip()]
                
                content = PromptContent(
                    title=title or prompt_text[:50],
                    prompt_text=prompt_text,
                    tags=tags,
                    upvotes=0
                )
                prompts.append(content)
        
        self.logger.info(f"从 {self.input_file} 读取到 {len(prompts)} 条 Prompt")
        return prompts
    
    def filter_duplicates(self, prompts: List[PromptContent]) -> List[PromptContent]:
        """
        过滤重复的 Prompt
        
        Args:
            prompts: 原始 Prompt 列表
            
        Returns:
            去重后的 Prompt 列表
        """
        unique_prompts = []
        seen_texts: Set[str] = set()
        
        for prompt in prompts:
            text_hash = hash(prompt.prompt_text.strip().lower())
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_prompts.append(prompt)
            else:
                self.logger.debug(f"跳过重复 Prompt: {prompt.prompt_text[:50]}...")
        
        duplicates = len(prompts) - len(unique_prompts)
        if duplicates > 0:
            self.logger.info(f"过滤了 {duplicates} 条重复 Prompt")
        
        return unique_prompts
    
    def filter_invalid(self, prompts: List[PromptContent]) -> List[PromptContent]:
        """
        过滤无效的 Prompt
        
        Args:
            prompts: 原始 Prompt 列表
            
        Returns:
            有效 Prompt 列表
        """
        valid_prompts = []
        
        for prompt in prompts:
            if not prompt.prompt_text or not prompt.prompt_text.strip():
                self.logger.warning(f"跳过空 Prompt")
                continue
            
            if len(prompt.prompt_text.strip()) < 10:
                self.logger.warning(f"跳过过短 Prompt: {prompt.prompt_text}")
                continue
            
            if len(prompt.prompt_text.strip()) > 2000:
                self.logger.warning(f"跳过过长 Prompt: {prompt.prompt_text[:50]}...")
                continue
            
            valid_prompts.append(prompt)
        
        invalid = len(prompts) - len(valid_prompts)
        if invalid > 0:
            self.logger.info(f"过滤了 {invalid} 条无效 Prompt")
        
        return valid_prompts
    
    def process_batch(
        self,
        prompts: List[PromptContent]
    ) -> List[MusicPromptDocument]:
        """
        批量处理 Prompt
        
        Args:
            prompts: 待处理的 Prompt 列表
            
        Returns:
            处理后的 MusicPromptDocument 列表
        """
        if self.dry_run:
            return self._mock_process(prompts)
        
        results = []
        batch_result = self.provider.process_batch(prompts)
        
        for i, result in enumerate(batch_result.results):
            if result.success and result.data:
                try:
                    doc = self._create_document(prompts[i], result.data)
                    results.append(doc)
                except Exception as e:
                    self.logger.error(f"创建文档失败 [{i}]: {e}")
                    self.failed_prompts.append(prompts[i].prompt_text)
            else:
                self.logger.error(f"处理失败 [{i}]: {result.error}")
                self.failed_prompts.append(prompts[i].prompt_text)
        
        return results
    
    def _mock_process(self, prompts: List[PromptContent]) -> List[MusicPromptDocument]:
        """模拟处理（试运行模式）"""
        docs = []
        for prompt in prompts[:5]:
            doc = MusicPromptDocument(
                original_prompt=prompt.prompt_text,
                translated_prompt=f"[模拟翻译] {prompt.prompt_text[:50]}",
                title=BilingualText(
                    en=prompt.title or "Mock Title",
                    zh=f"[模拟标题] {prompt.title or 'Mock'}"
                ),
                prompt=BilingualText(
                    en=prompt.prompt_text,
                    zh=f"[模拟翻译] {prompt.prompt_text[:100]}"
                ),
                genre=MusicGenre.ELECTRONIC,
                tags=prompt.tags,
                douyin_tags=["模拟", "测试"],
                dsp_params=DSPParameters(
                    bpm=128,
                    key="C Major",
                    energy_level=EnergyLevel.MEDIUM
                ),
                gem_suggestion="[模拟建议] 这是一个试运行模式的模拟输出",
                viral_score=50.0
            )
            docs.append(doc)
        return docs
    
    def _create_document(
        self,
        prompt: PromptContent,
        data: Dict[str, Any]
    ) -> MusicPromptDocument:
        """
        从处理结果创建 MusicPromptDocument
        
        Args:
            prompt: 原始 Prompt
            data: AI 返回的数据
            
        Returns:
            MusicPromptDocument 实例
        """
        import hashlib
        
        # 生成唯一 ID
        content_hash = hashlib.md5(
            (prompt.prompt_text + data.get("prompt_zh", "")).encode()
        ).hexdigest()[:12]
        doc_id = f"vmdp_{content_hash}"
        
        genre_str = data.get("genre", "other").lower()
        try:
            genre = MusicGenre(genre_str)
        except ValueError:
            genre = MusicGenre.OTHER
        
        # 先获取 dsp_data
        dsp_data = data.get("dsp_params", {})
        
        # 处理 energy_level，处理 Qwen 可能返回的无效值
        energy_level_str = dsp_data.get("energy_level", "medium") if dsp_data else "medium"
        # 清理无效值
        invalid_values = ['high-very_high', 'n/a', 'N/A', '未指定', 'unknown', 'none', '']
        if energy_level_str in invalid_values or not energy_level_str:
            energy_level_str = "medium"
        # 映射常见错误
        energy_mapping = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'very_high': 'very_high',
            'veryhigh': 'very_high',
            'very high': 'very_high',
        }
        energy_level_str = energy_mapping.get(energy_level_str.lower(), "medium")
        
        try:
            energy_level = EnergyLevel(energy_level_str)
        except ValueError:
            energy_level = EnergyLevel.MEDIUM
        
        # 处理 BPM - 确保在有效范围内
        bpm = dsp_data.get("bpm")
        if bpm is not None:
            try:
                bpm = int(bpm)
                if bpm < 40:
                    bpm = 40
                elif bpm > 250:
                    bpm = 250
            except (ValueError, TypeError):
                bpm = None
        
        dsp_params = DSPParameters(
            bpm=bpm,
            key=dsp_data.get("key"),
            energy_level=energy_level,
            frequency_center=dsp_data.get("frequency_center"),
            dynamics_range=dsp_data.get("dynamics_range"),
            reverb=dsp_data.get("reverb"),
            compression=dsp_data.get("compression")
        )
        
        # 处理空值 - 如果中文翻译为空，使用英文原文
        title_zh = data.get("title_zh", "").strip()
        prompt_zh = data.get("prompt_zh", "").strip()
        
        if not title_zh:
            title_zh = prompt.title or prompt.prompt_text[:50]
        if not prompt_zh:
            prompt_zh = prompt.prompt_text
        
        doc = MusicPromptDocument(
            id=doc_id,
            original_prompt=prompt.prompt_text,
            translated_prompt=prompt_zh,
            title=BilingualText(
                en=prompt.title or prompt.prompt_text[:50],
                zh=title_zh
            ),
            prompt=BilingualText(
                en=prompt.prompt_text,
                zh=prompt_zh
            ),
            genre=genre,
            tags=prompt.tags,
            douyin_tags=data.get("douyin_tags", []),
            dsp_params=dsp_params,
            gem_suggestion=data.get("gem_suggestion", ""),
            viral_score=0.0,
            source=SourceInfo(
                platform="cold_start",
                collected_at=datetime.now()
            )
        )
        
        doc.viral_score = doc.calculate_viral_score(
            upvotes=prompt.upvotes,
            tag_count=len(doc.douyin_tags),
            prompt_length=len(doc.translated_prompt)
        )
        
        return doc
    
    def save_by_genre(self, documents: List[MusicPromptDocument]) -> None:
        """
        按流派保存文档（支持层级分类）
        
        层级存储结构：
        data/genres/
        ├── electronic/
        │   ├── bass/
        │   │   ├── trap.json
        │   │   ├── dubstep.json
        │   │   └── hardstyle.json
        │   ├── house.json
        │   ├── trance.json
        │   └── else.json
        ├── hip_hop/
        │   ├── trap.json
        │   └── boombap.json
        └── [其他流派].json
        
        Args:
            documents: 文档列表
        """
        GENRES_DIR.mkdir(parents=True, exist_ok=True)
        
        genre_docs: Dict[str, List[MusicPromptDocument]] = {}
        for doc in documents:
            genre_value = doc.genre.value
            if genre_value not in genre_docs:
                genre_docs[genre_value] = []
            genre_docs[genre_value].append(doc)
        
        for genre_value, docs in genre_docs.items():
            genre_file = self._get_genre_file_path(genre_value)
            genre_file.parent.mkdir(parents=True, exist_ok=True)
            
            existing_docs = []
            if genre_file.exists():
                try:
                    with open(genre_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_docs = data.get("documents", [])
                except Exception as e:
                    self.logger.warning(f"读取现有文件失败 {genre_file}: {e}")
            
            for doc in docs:
                doc_dict = json.loads(doc.to_json_str())
                existing_docs.append(doc_dict)
            
            collection = {
                "genre": genre_value,
                "count": len(existing_docs),
                "documents": existing_docs,
                "updated_at": datetime.now().isoformat()
            }
            
            with open(genre_file, 'w', encoding='utf-8') as f:
                json.dump(collection, f, ensure_ascii=False, indent=2)
            
            self.genre_counts[genre_value] = self.genre_counts.get(genre_value, 0) + len(docs)
            self.logger.info(f"已保存 {len(docs)} 条到 {genre_file}")
    
    def _get_genre_file_path(self, genre_value: str) -> Path:
        """
        根据流派值获取文件路径（支持层级）
        
        Args:
            genre_value: 流派值，如 "electronic.bass.dubstep" 或 "cinematic"
            
        Returns:
            文件路径
        """
        parts = genre_value.split('.')
        
        if len(parts) == 1:
            return GENRES_DIR / f"{parts[0]}.json"
        elif len(parts) == 2:
            return GENRES_DIR / parts[0] / f"{parts[1]}.json"
        elif len(parts) >= 3:
            return GENRES_DIR / parts[0] / parts[1] / f"{parts[2]}.json"
        else:
            return GENRES_DIR / f"{genre_value}.json"
    
    def run(self) -> Dict[str, Any]:
        """
        执行冷启动处理
        
        Returns:
            处理统计信息
        """
        start_time = time.time()
        
        self.logger.info("=" * 60)
        self.logger.info("MUSICprompt 冷启动炼金脚本启动")
        self.logger.info("=" * 60)
        
        prompts = self.read_prompts()
        
        prompts = self.filter_duplicates(prompts)
        prompts = self.filter_invalid(prompts)
        
        if not prompts:
            self.logger.warning("没有有效的 Prompt 需要处理")
            return {"status": "no_prompts", "total": 0}
        
        self.logger.info(f"待处理 Prompt 数量: {len(prompts)}")
        
        total_processed = 0
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(prompts), self.batch_size):
            batch = prompts[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(prompts) + self.batch_size - 1) // self.batch_size
            
            self.logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 条)")
            
            try:
                documents = self.process_batch(batch)
                self.save_by_genre(documents)
                
                total_processed += len(batch)
                total_success += len(documents)
                total_failed += len(batch) - len(documents)
                
                for doc in documents:
                    self.processed_ids.add(doc.id)
                
                self.logger.info(f"批次 {batch_num} 完成: 成功 {len(documents)}/{len(batch)}")
                
            except Exception as e:
                self.logger.error(f"批次 {batch_num} 处理失败: {e}")
                total_failed += len(batch)
                self.failed_prompts.extend([p.prompt_text for p in batch])
        
        self._save_processed_ids()
        
        if self.failed_prompts:
            self._save_failed_prompts()
        
        elapsed_time = time.time() - start_time
        
        stats = {
            "status": "completed",
            "total_prompts": len(prompts),
            "total_processed": total_processed,
            "total_success": total_success,
            "total_failed": total_failed,
            "success_rate": f"{(total_success / total_processed * 100):.1f}%" if total_processed > 0 else "0%",
            "elapsed_time": f"{elapsed_time:.1f}s",
            "genre_distribution": {g.value: c for g, c in self.genre_counts.items()},
            "dry_run": self.dry_run
        }
        
        self.logger.info("=" * 60)
        self.logger.info("处理完成")
        self.logger.info(f"总处理: {total_processed}")
        self.logger.info(f"成功: {total_success}")
        self.logger.info(f"失败: {total_failed}")
        self.logger.info(f"耗时: {elapsed_time:.1f}s")
        self.logger.info("=" * 60)
        
        return stats
    
    def _save_failed_prompts(self) -> None:
        """保存失败的 Prompt"""
        failed_file = PROCESSED_DIR / "failed_prompts.txt"
        with open(failed_file, 'w', encoding='utf-8') as f:
            for prompt in self.failed_prompts:
                f.write(f"{prompt}\n")
        self.logger.info(f"已保存 {len(self.failed_prompts)} 条失败 Prompt 到 {failed_file}")


def create_sample_prompts(output_file: str, count: int = 50) -> None:
    """
    创建示例 Prompt 文件
    
    Args:
        output_file: 输出文件路径
        count: 生成的 Prompt 数量
    """
    sample_prompts = [
        "Epic cinematic orchestral trailer music with powerful brass and soaring strings, building tension to an explosive climax",
        "Lo-fi hip hop beat with jazzy piano samples, vinyl crackle, and a chill nostalgic vibe for studying",
        "Dark trap beat with heavy 808 bass, aggressive hi-hats, and ominous synth melodies",
        "Uplifting progressive house with euphoric melodies, driving bassline, and festival-ready drops",
        "Ambient soundscape with ethereal pads, gentle piano, and nature sounds for meditation",
        "Aggressive dubstep with distorted bass, sharp sound design, and heavy drops",
        "Smooth R&B with silky vocals, groovy bass, and lush harmonies",
        "Folk acoustic ballad with heartfelt lyrics, gentle guitar picking, and warm production",
        "High-energy EDM festival anthem with massive drops, soaring vocals, and hands-in-the-air moments",
        "Jazz fusion with complex harmonies, virtuosic solos, and intricate rhythms",
        "Dark techno with hypnotic rhythms, industrial textures, and minimal arrangements",
        "Dreamy synthwave with retro 80s aesthetics, pulsing basslines, and nostalgic melodies",
        "Heavy metal with crushing riffs, thunderous drums, and aggressive vocals",
        "Chill electronic with soft synths, gentle beats, and atmospheric textures",
        "World music fusion combining traditional instruments with modern electronic production",
        "Deep house with soulful vocals, warm pads, and groovy basslines",
        "Experimental electronic with glitchy textures, unconventional rhythms, and abstract sound design",
        "Romantic piano ballad with emotional melodies and orchestral accompaniment",
        "Funky disco with infectious grooves, brass sections, and danceable rhythms",
        "Atmospheric drum and bass with rolling breaks, deep bass, and ethereal pads",
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for prompt in sample_prompts[:count]:
            f.write(f"{prompt}\n")
    
    print(f"已创建示例文件: {output_file} ({min(count, len(sample_prompts))} 条)")


def main():
    parser = argparse.ArgumentParser(
        description="MUSICprompt 冷启动炼金脚本 - 批量处理原始 Prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python tools/cold_start_alchemist.py
    python tools/cold_start_alchemist.py --input my_prompts.txt --batch-size 10
    python tools/cold_start_alchemist.py --dry-run
    python tools/cold_start_alchemist.py --create-sample
        """
    )
    parser.add_argument(
        '--input', '-i',
        default=DEFAULT_INPUT_FILE,
        help=f'输入文件路径 (默认: {DEFAULT_INPUT_FILE})'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=BATCH_SIZE,
        help=f'批处理大小 (默认: {BATCH_SIZE})'
    )
    parser.add_argument(
        '--api-key', '-k',
        help='API Key (根据 --provider 自动选择环境变量)'
    )
    parser.add_argument(
        '--provider', '-p',
        default='gemini',
        choices=['gemini', 'siliconflow'],
        help='AI 提供者 (默认: gemini, 可选: siliconflow 极速模式)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式，不调用 API'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='创建示例 Prompt 文件'
    )
    parser.add_argument(
        '--sample-count',
        type=int,
        default=50,
        help='示例 Prompt 数量 (默认: 50)'
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_prompts(args.input, args.sample_count)
        return
    
    masker = setup_secure_logging(
        level=logging.INFO,
        log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    logger = logging.getLogger("main")
    logger.info("MUSICprompt 冷启动炼金脚本")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"批处理大小: {args.batch_size}")
    logger.info(f"提供者: {args.provider}")
    logger.info(f"试运行模式: {args.dry_run}")
    
    try:
        alchemist = ColdStartAlchemist(
            input_file=args.input,
            batch_size=args.batch_size,
            api_key=args.api_key,
            dry_run=args.dry_run,
            provider=args.provider
        )
        
        if not args.dry_run:
            alchemist.initialize_provider(args.api_key)
        
        stats = alchemist.run()
        
        print("\n" + "=" * 60)
        print("处理统计")
        print("=" * 60)
        for key, value in stats.items():
            print(f"{key}: {value}")
        
    except KeyboardInterrupt:
        logger.warning("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
