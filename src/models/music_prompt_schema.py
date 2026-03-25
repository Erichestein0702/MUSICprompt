"""
MUSICprompt 数据模型定义

使用 Pydantic v2 定义 MUSICprompt 文档的标准数据结构，
包含原始 Prompt、翻译、DSP 参数、爆款指数等核心字段。

流派分类采用层级结构：
- electronic (电子音乐)
  ├── bass (Bass 音乐)
  │   ├── trap (EDM Trap)
  │   ├── dubstep (Dubstep)
  │   └── hardstyle (Hardstyle)
  ├── house (House)
  ├── trance (Trance)
  └── else (其他电子)
- hip_hop (嘻哈)
  ├── trap (Trap)
  └── boombap (Boom Bap)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib


class EnergyLevel(str, Enum):
    """能量等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MusicGenre(str, Enum):
    """
    音乐流派分类 - 层级结构
    
    格式：父类.子类.孙类
    
    主要分类：
    - electronic: 电子音乐（含 bass/house/trance/else）
    - hip_hop: 嘻哈（含 trap/boombap）
    - cinematic: 电影配乐
    - pop: 流行
    - rock: 摇滚
    - ambient: 氛围音乐
    - classical: 古典
    - jazz: 爵士
    - rnb: R&B
    - lo_fi: 低保真
    - folk: 民谣
    - world: 世界音乐
    - experimental: 实验音乐
    - other: 其他
    """
    
    # ========== 电子音乐 (Electronic) ==========
    # Electronic > Bass
    ELECTRONIC_BASS_TRAP = "electronic.bass.trap"
    ELECTRONIC_BASS_DUBSTEP = "electronic.bass.dubstep"
    ELECTRONIC_BASS_HARDSTYLE = "electronic.bass.hardstyle"
    ELECTRONIC_BASS = "electronic.bass"
    
    # Electronic > House
    ELECTRONIC_HOUSE = "electronic.house"
    
    # Electronic > Trance
    ELECTRONIC_TRANCE = "electronic.trance"
    
    # Electronic > Phonk & Funk
    ELECTRONIC_PHONK_FUNK = "electronic.phonk_funk"
    
    # Electronic > Techno
    ELECTRONIC_TECHNO = "electronic.techno"
    
    # Electronic > Else (其他电子：Electro, DnB 等)
    ELECTRONIC_ELSE = "electronic.else"
    
    # Electronic 根类
    ELECTRONIC = "electronic"
    
    # ========== 嘻哈 (Hip Hop) ==========
    HIP_HOP_TRAP = "hip_hop.trap"
    HIP_HOP_BOOMBAP = "hip_hop.boombap"
    HIP_HOP = "hip_hop"
    
    # ========== 其他主类 ==========
    CINEMATIC = "cinematic"
    POP = "pop"
    ROCK = "rock"
    AMBIENT = "ambient"
    CLASSICAL = "classical"
    JAZZ = "jazz"
    RNB = "rnb"
    LO_FI = "lo_fi"
    FOLK = "folk"
    WORLD = "world"
    EXPERIMENTAL = "experimental"
    OTHER = "other"
    
    @classmethod
    def get_parent(cls, genre: 'MusicGenre') -> Optional['MusicGenre']:
        """获取父级流派"""
        value = genre.value
        parts = value.split('.')
        if len(parts) > 1:
            parent_value = '.'.join(parts[:-1])
            try:
                return cls(parent_value)
            except ValueError:
                return None
        return None
    
    @classmethod
    def get_children(cls, genre: 'MusicGenre') -> List['MusicGenre']:
        """获取子级流派"""
        children = []
        prefix = genre.value + '.'
        for g in cls:
            if g.value.startswith(prefix) and g.value.count('.') == genre.value.count('.') + 1:
                children.append(g)
        return children
    
    @classmethod
    def get_all_electronic(cls) -> List['MusicGenre']:
        """获取所有电子音乐子类"""
        return [g for g in cls if g.value.startswith('electronic')]
    
    @classmethod
    def get_all_hip_hop(cls) -> List['MusicGenre']:
        """获取所有嘻哈子类"""
        return [g for g in cls if g.value.startswith('hip_hop')]


GENRE_DISPLAY_NAMES = {
    # 电子音乐
    "electronic": "电子音乐",
    "electronic.bass": "Bass 音乐",
    "electronic.bass.trap": "EDM Trap",
    "electronic.bass.dubstep": "Dubstep",
    "electronic.bass.hardstyle": "Hardstyle",
    "electronic.house": "House",
    "electronic.trance": "Trance",
    "electronic.phonk_funk": "Phonk & Funk",
    "electronic.techno": "Techno",
    "electronic.else": "其他电子",
    
    # 嘻哈
    "hip_hop": "嘻哈",
    "hip_hop.trap": "Trap",
    "hip_hop.boombap": "Boom Bap",
    
    # 其他
    "cinematic": "电影配乐",
    "pop": "流行",
    "rock": "摇滚",
    "ambient": "氛围音乐",
    "classical": "古典",
    "jazz": "爵士",
    "rnb": "R&B",
    "lo_fi": "低保真",
    "folk": "民谣",
    "world": "世界音乐",
    "experimental": "实验音乐",
    "other": "其他",
}


class DSPParameters(BaseModel):
    """DSP 参数模型 - 音频工程参数"""
    bpm: Optional[int] = Field(
        None,
        ge=40,
        le=220,
        description="节拍速度 (Beats Per Minute)"
    )
    key: Optional[str] = Field(
        None,
        description="调性，如 C Major, A Minor, D Dorian"
    )
    energy_level: EnergyLevel = Field(
        EnergyLevel.MEDIUM,
        description="能量等级：low/medium/high/very_high"
    )
    frequency_center: Optional[str] = Field(
        None,
        description="频率中心范围，如 200Hz-2kHz"
    )
    dynamics_range: Optional[str] = Field(
        None,
        description="动态范围，如 Wide (40dB), Narrow (10dB)"
    )
    reverb: Optional[str] = Field(
        None,
        description="混响建议，如 Large Hall, Small Room, Plate"
    )
    compression: Optional[str] = Field(
        None,
        description="压缩建议，如 Aggressive, Gentle, Parallel"
    )
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip().title()


class BilingualText(BaseModel):
    """双语文本模型"""
    en: str = Field(..., description="英文原文")
    zh: str = Field(..., description="中文翻译")
    
    @field_validator('en', 'zh')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("文本不能为空")
        return v.strip()


class SourceInfo(BaseModel):
    """来源信息"""
    platform: str = Field(default="reddit", description="来源平台")
    url: Optional[str] = Field(None, description="原始链接")
    author: Optional[str] = Field(None, description="作者")
    collected_at: datetime = Field(
        default_factory=datetime.now,
        description="采集时间"
    )


class MusicPromptDocument(BaseModel):
    """MUSICprompt 标准文档模型"""
    
    id: str = Field(..., description="文档唯一标识")
    version: str = Field(default="1.0.0", description="MUSICprompt 协议版本")
    
    original_prompt: str = Field(..., description="原始英文 Prompt")
    translated_prompt: str = Field(..., description="翻译后的中文 Prompt")
    
    title: BilingualText = Field(..., description="双语标题")
    prompt: BilingualText = Field(..., description="双语 Prompt 内容")
    
    genre: MusicGenre = Field(
        default=MusicGenre.OTHER,
        description="音乐流派分类"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="原始风格标签"
    )
    douyin_tags: List[str] = Field(
        default_factory=list,
        description="抖音平台标签"
    )
    
    dsp_params: DSPParameters = Field(
        default_factory=DSPParameters,
        description="DSP 参数"
    )
    
    gem_suggestion: str = Field(
        default="",
        description="Gem 专业音频处理建议"
    )
    
    viral_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="爆款指数 (0-100)"
    )
    
    source: Optional[SourceInfo] = Field(
        default=None,
        description="来源信息"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    
    @model_validator(mode='after')
    @classmethod
    def generate_id_if_missing(cls, data: 'MusicPromptDocument') -> 'MusicPromptDocument':
        if not data.id:
            content_hash = hashlib.md5(
                (data.original_prompt + data.translated_prompt).encode()
            ).hexdigest()[:12]
            data.id = f"musicprompt_{content_hash}"
        return data
    
    def calculate_viral_score(
        self,
        upvotes: int = 0,
        tag_count: int = 0,
        prompt_length: int = 0
    ) -> float:
        """
        计算爆款指数
        
        公式：0.4 * (upvotes/10) + 0.3 * (tag_count * 5) + 0.3 * (prompt_length/100)
        """
        score = min(
            0.4 * (upvotes / 10) +
            0.3 * tag_count * 5 +
            0.3 * (prompt_length / 100),
            100.0
        )
        return round(score, 1)
    
    def to_json_str(self, indent: int = 2) -> str:
        """导出为 JSON 字符串"""
        return self.model_dump_json(indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicPromptDocument':
        """从字典创建实例"""
        return cls.model_validate(data)
    
    def get_genre_display_name(self) -> str:
        """获取流派显示名称"""
        return GENRE_DISPLAY_NAMES.get(self.genre.value, self.genre.value)


class MusicPromptDocumentCollection(BaseModel):
    """MUSICprompt 文档集合"""
    documents: List[MusicPromptDocument] = Field(default_factory=list)
    total_count: int = Field(default=0, description="文档总数")
    processed_at: datetime = Field(
        default_factory=datetime.now,
        description="处理时间"
    )
    
    def add(self, doc: MusicPromptDocument) -> None:
        """添加文档"""
        self.documents.append(doc)
        self.total_count = len(self.documents)
    
    def get_by_genre(self, genre: MusicGenre) -> List[MusicPromptDocument]:
        """按流派筛选"""
        return [doc for doc in self.documents if doc.genre == genre]
    
    def get_by_genre_prefix(self, prefix: str) -> List[MusicPromptDocument]:
        """按流派前缀筛选（支持层级查询）"""
        return [doc for doc in self.documents if doc.genre.value.startswith(prefix)]
    
    def get_all_electronic(self) -> List[MusicPromptDocument]:
        """获取所有电子音乐文档"""
        return self.get_by_genre_prefix("electronic")
    
    def get_all_hip_hop(self) -> List[MusicPromptDocument]:
        """获取所有嘻哈文档"""
        return self.get_by_genre_prefix("hip_hop")
    
    def get_top_viral(self, n: int = 10) -> List[MusicPromptDocument]:
        """获取爆款指数最高的 N 个"""
        return sorted(
            self.documents,
            key=lambda x: x.viral_score,
            reverse=True
        )[:n]
    
    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON"""
        return self.model_dump_json(indent=indent)


class RawPromptEntry(BaseModel):
    """原始 Prompt 条目"""
    prompt: str = Field(..., description="Prompt 文本")
    title: Optional[str] = Field(None, description="标题")
    tags: List[str] = Field(default_factory=list, description="标签")
    upvotes: int = Field(default=0, description="点赞数")
    source_url: Optional[str] = Field(None, description="来源链接")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt 不能为空")
        return v.strip()
    
    def is_valid(self) -> bool:
        """检查是否有效"""
        return bool(self.prompt and self.prompt.strip())


class GenreStats(BaseModel):
    """流派统计信息"""
    genre: MusicGenre
    count: int = 0
    avg_viral_score: float = 0.0
    top_prompts: List[str] = Field(default_factory=list)
    
    def update(self, docs: List[MusicPromptDocument]) -> None:
        """更新统计"""
        self.count = len(docs)
        if docs:
            self.avg_viral_score = sum(d.viral_score for d in docs) / len(docs)
            sorted_docs = sorted(docs, key=lambda x: x.viral_score, reverse=True)
            self.top_prompts = [d.title.zh if d.title else d.id for d in sorted_docs[:5]]
