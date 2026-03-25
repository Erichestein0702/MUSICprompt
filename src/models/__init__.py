"""
VMDP 数据模型模块
"""

from .vmdp_schema import (
    VMDPDocument,
    DSPParameters,
    BilingualText,
    MusicGenre,
    EnergyLevel,
    VMDPDocumentCollection,
    RawPromptEntry,
    GenreStats,
    SourceInfo,
    GENRE_DISPLAY_NAMES,
)

__all__ = [
    "VMDPDocument",
    "DSPParameters",
    "BilingualText",
    "MusicGenre",
    "EnergyLevel",
    "VMDPDocumentCollection",
    "RawPromptEntry",
    "GenreStats",
    "SourceInfo",
    "GENRE_DISPLAY_NAMES",
]

__version__ = "1.0.0"
