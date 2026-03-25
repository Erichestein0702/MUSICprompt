"""
MUSICprompt 数据模型模块

提供 MUSICprompt 项目的核心数据结构：
- MusicPromptDocument: 标准文档模型
- MusicPromptDocumentCollection: 文档集合
- DSPParameters: DSP 参数
- BilingualText: 双语文本
- MusicGenre: 音乐流派枚举
- EnergyLevel: 能量等级
"""

from .music_prompt_schema import (
    DSPParameters,
    BilingualText,
    MusicGenre,
    EnergyLevel,
    MusicPromptDocument,
    MusicPromptDocumentCollection,
    RawPromptEntry,
    GenreStats,
    SourceInfo,
    GENRE_DISPLAY_NAMES,
)

__all__ = [
    "DSPParameters",
    "BilingualText",
    "MusicGenre",
    "EnergyLevel",
    "MusicPromptDocument",
    "MusicPromptDocumentCollection",
    "RawPromptEntry",
    "GenreStats",
    "SourceInfo",
    "GENRE_DISPLAY_NAMES",
]
