"""MUSICprompt v2 数据协议。

v2 将文本质量、生成效果与参数来源分开，避免把规则评分当成音乐效果，
也避免把模型推断的参数当成原始 Prompt 中明确存在的事实。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

SCHEMA_VERSION = "2.0.0"


class ParameterOrigin(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    TESTED = "tested"
    VERIFIED = "verified"


class SourceAttribution(BaseModel):
    name: str = ""
    url: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    raw: Optional[str] = None


class GenerationEvaluation(BaseModel):
    platform: str
    model_version: Optional[str] = None
    audio_url: Optional[str] = None
    generation_score: Optional[float] = Field(default=None, ge=0, le=10)
    ratings: Dict[str, float] = Field(default_factory=dict)
    notes: str = ""
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("ratings")
    @classmethod
    def validate_ratings(cls, value: Dict[str, float]) -> Dict[str, float]:
        for dimension, score in value.items():
            if not 0 <= score <= 10:
                raise ValueError(f"评分维度 {dimension} 必须在 0-10 之间")
        return value


_BPM_PATTERN = re.compile(
    r"(?:\b(?:bpm|tempo)\s*[:=]?\s*(\d{2,3})\b)|(?:\b(\d{2,3})\s*bpm\b)",
    re.IGNORECASE,
)
_KEY_PATTERN = re.compile(
    r"\b([A-Ga-g](?:#|b)?\s+(?:major|minor|dorian|phrygian|lydian|mixolydian|locrian))\b",
    re.IGNORECASE,
)


def extract_explicit_bpm(text: str) -> Optional[int]:
    """只提取文本明确标出的 BPM，不进行风格推断。"""
    match = _BPM_PATTERN.search(text or "")
    if not match:
        return None
    value = int(match.group(1) or match.group(2))
    return value if 40 <= value <= 220 else None


def extract_explicit_key(text: str) -> Optional[str]:
    """只提取带根音和调式的调性，如 F minor 或 C# major。"""
    match = _KEY_PATTERN.search(text or "")
    if not match:
        return None
    root, mode = match.group(1).split(None, 1)
    return f"{root.upper()} {mode.lower()}"


def _clean_tags(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        cleaned = str(value).strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


class MusicPromptV2(BaseModel):
    schema_version: Literal["2.0.0"] = SCHEMA_VERSION
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    title_zh: str = ""
    style_prompt: str = Field(min_length=1)
    style_prompt_zh: str = ""
    lyrics_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None

    target_platform: str = "unknown"
    target_model: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    instruments: List[str] = Field(default_factory=list)
    moods: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)

    bpm: Optional[int] = Field(default=None, ge=40, le=220)
    bpm_origin: ParameterOrigin = ParameterOrigin.UNKNOWN
    key_signature: Optional[str] = None
    key_origin: ParameterOrigin = ParameterOrigin.UNKNOWN

    text_quality_score: float = Field(default=0, ge=0, le=10)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    evaluations: List[GenerationEvaluation] = Field(default_factory=list)
    source: SourceAttribution = Field(default_factory=SourceAttribution)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator(
        "genres", "instruments", "moods", "use_cases", mode="before"
    )
    @classmethod
    def normalize_tags(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        return _clean_tags(value)

    @field_validator("title", "style_prompt")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("必填文本不能为空")
        return value

    @model_validator(mode="after")
    def validate_parameter_origins(self) -> "MusicPromptV2":
        if self.bpm is not None and self.bpm_origin == ParameterOrigin.UNKNOWN:
            self.bpm_origin = ParameterOrigin.EXPLICIT
        if self.bpm is None:
            self.bpm_origin = ParameterOrigin.UNKNOWN
        if self.key_signature is not None and self.key_origin == ParameterOrigin.UNKNOWN:
            self.key_origin = ParameterOrigin.EXPLICIT
        if self.key_signature is None:
            self.key_origin = ParameterOrigin.UNKNOWN
        if self.verification_status == VerificationStatus.VERIFIED and not self.evaluations:
            raise ValueError("verified 状态必须至少包含一条生成评测记录")
        return self

    @property
    def generation_score(self) -> Optional[float]:
        scores = [
            item.generation_score
            for item in self.evaluations
            if item.generation_score is not None
        ]
        return round(sum(scores) / len(scores), 2) if scores else None

    @classmethod
    def from_legacy(cls, legacy: Dict[str, Any]) -> "MusicPromptV2":
        """从 v1 JSON/SQLite 字典迁移，并补提取原文明确参数。"""
        prompt_text = legacy.get("prompt_text") or legacy.get("style_prompt") or ""
        bpm = legacy.get("bpm") or extract_explicit_bpm(prompt_text)
        key_signature = (
            legacy.get("key_signature")
            or legacy.get("key")
            or extract_explicit_key(prompt_text)
        )
        translation_meta = legacy.get("translation_meta") or {}
        source_value = legacy.get("source") or ""
        if isinstance(source_value, dict):
            source = SourceAttribution.model_validate(source_value)
        else:
            source = SourceAttribution(
                name=str(source_value).split("/")[0] if source_value else "",
                raw=str(source_value) or None,
            )
        return cls(
            id=legacy["id"],
            title=legacy.get("title") or "Untitled",
            title_zh=legacy.get("title_zh")
            or translation_meta.get("title_zh", ""),
            style_prompt=prompt_text,
            style_prompt_zh=legacy.get("prompt_zh")
            or legacy.get("style_prompt_zh", ""),
            lyrics_prompt=legacy.get("lyrics_prompt"),
            negative_prompt=legacy.get("negative_prompt"),
            target_platform=legacy.get("target_platform")
            or legacy.get("platform")
            or "unknown",
            target_model=legacy.get("target_model"),
            genres=legacy.get("genres") or legacy.get("genre") or [],
            instruments=legacy.get("instruments") or [],
            moods=legacy.get("moods")
            or translation_meta.get("mood_keywords_zh", []),
            use_cases=legacy.get("use_cases") or [],
            bpm=bpm,
            bpm_origin=ParameterOrigin.EXPLICIT if bpm is not None else ParameterOrigin.UNKNOWN,
            key_signature=key_signature,
            key_origin=ParameterOrigin.EXPLICIT if key_signature else ParameterOrigin.UNKNOWN,
            text_quality_score=legacy.get("text_quality_score")
            if legacy.get("text_quality_score") is not None
            else legacy.get("quality_score", 0),
            source=source,
            created_at=legacy.get("created_at"),
            updated_at=legacy.get("updated_at"),
        )

    def to_legacy(self) -> Dict[str, Any]:
        """生成旧工具仍可消费的字典，并附带 v2 字段。"""
        return {
            "id": self.id,
            "title": self.title,
            "title_zh": self.title_zh,
            "prompt_text": self.style_prompt,
            "prompt_zh": self.style_prompt_zh,
            "platform": self.target_platform,
            "genre": self.genres,
            "instruments": self.instruments,
            "use_cases": self.use_cases,
            "quality_score": self.text_quality_score,
            "text_quality_score": self.text_quality_score,
            "bpm": self.bpm,
            "bpm_origin": self.bpm_origin.value,
            "key": self.key_signature,
            "key_signature": self.key_signature,
            "key_origin": self.key_origin.value,
            "schema_version": self.schema_version,
            "target_model": self.target_model,
            "lyrics_prompt": self.lyrics_prompt,
            "negative_prompt": self.negative_prompt,
            "generation_score": self.generation_score,
            "verification_status": self.verification_status.value,
            "source": self.source.raw or self.source.name,
            "source_url": self.source.url,
            "source_license": self.source.license,
            "translation_meta": {"mood_keywords_zh": self.moods},
        }
