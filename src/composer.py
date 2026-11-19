"""确定性的音乐需求解析、Prompt 编译、局部 Remix 与差异比较。"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MusicBrief(BaseModel):
    genre: str = "pop"
    mood: str = "emotional"
    use_case: Optional[str] = None
    bpm: Optional[int] = Field(default=None, ge=40, le=220)
    key: Optional[str] = None
    vocals: Optional[str] = None
    language: Optional[str] = None
    instruments: List[str] = Field(default_factory=list)
    structure: List[str] = Field(default_factory=list)
    production: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)
    extra: Optional[str] = None

    @field_validator("structure", "instruments", "production", "avoid")
    @classmethod
    def clean_list(cls, values: List[str]) -> List[str]:
        result = []
        for value in values:
            value = value.strip()
            if value and value.casefold() not in {v.casefold() for v in result}:
                result.append(value)
        return result


class CompiledPrompt(BaseModel):
    platform: str
    brief: MusicBrief
    style_prompt: str
    negative_prompt: str = ""
    structure_prompt: str = ""
    warnings: List[str] = Field(default_factory=list)


_GENRES = {
    "流行": "pop", "独立流行": "indie pop", "摇滚": "rock",
    "电子": "electronic", "嘻哈": "hip hop", "说唱": "rap",
    "爵士": "jazz", "民谣": "folk", "乡村": "country",
    "氛围": "ambient", "古典": "classical", "放克": "funk",
    "蓝调": "blues", "金属": "metal", "朋克": "punk",
}
_MOODS = {
    "克制": "restrained", "治愈": "healing", "忧郁": "melancholic",
    "明亮": "uplifting", "黑暗": "dark", "浪漫": "romantic",
    "激昂": "anthemic", "松弛": "laid-back", "紧张": "tense",
}
_USE_CASES = {
    "开车": "night drive", "学习": "study and focus", "健身": "workout",
    "派对": "party", "睡眠": "sleep", "冥想": "meditation",
    "游戏": "gaming", "影视": "cinematic", "雨夜": "rainy night",
}
_VOCALS = {
    "女声": "female vocals", "男声": "male vocals",
    "合唱": "layered vocal harmonies", "纯音乐": "instrumental",
}
_INSTRUMENTS = {
    "钢琴": "piano", "吉他": "guitar", "贝斯": "bass",
    "鼓": "drums", "合成器": "synthesizer", "弦乐": "strings",
    "萨克斯": "saxophone", "小提琴": "violin", "大提琴": "cello",
}


def _contains(text: str, mapping: Dict[str, str]) -> Optional[str]:
    for key in sorted(mapping, key=len, reverse=True):
        if key in text:
            return mapping[key]
    return None


def brief_from_text(text: str) -> MusicBrief:
    """从中文或中英混合描述中提取明确需求，保留原文作为补充约束。"""
    text = text.strip()
    if not text:
        raise ValueError("音乐需求不能为空")
    bpm_match = re.search(r"(\d{2,3})\s*(?:BPM|bpm)", text)
    key_match = re.search(
        r"\b([A-Ga-g](?:#|b)?\s*(?:major|minor|大调|小调))\b", text,
        re.IGNORECASE,
    )
    key = None
    if key_match:
        key = key_match.group(1).replace("大调", "major").replace("小调", "minor")
    instruments = [v for k, v in _INSTRUMENTS.items() if k in text]
    for instrument in _INSTRUMENTS.values():
        if instrument.casefold() in text.casefold() and instrument not in instruments:
            instruments.append(instrument)
    mood_parts = [v for k, v in _MOODS.items() if k in text]
    return MusicBrief(
        genre=_contains(text, _GENRES) or "pop",
        mood=", ".join(mood_parts) if mood_parts else "emotional",
        use_case=_contains(text, _USE_CASES),
        bpm=int(bpm_match.group(1)) if bpm_match else None,
        key=key,
        vocals=_contains(text, _VOCALS),
        language="Chinese" if "中文" in text else None,
        instruments=instruments,
        extra=text,
    )


def _warnings(brief: MusicBrief) -> List[str]:
    warnings = []
    if brief.bpm and brief.bpm < 75 and brief.genre in {"drum and bass", "hardstyle"}:
        warnings.append("当前 BPM 与所选高能量流派可能不协调")
    if brief.vocals == "instrumental" and brief.language:
        warnings.append("纯音乐与人声语言设置冲突，已保留字段，请确认需求")
    if brief.mood and "restrained" in brief.mood and "wall of sound" in brief.production:
        warnings.append("克制情绪与高密度 Wall of Sound 制作方向可能冲突")
    return warnings


def compile_prompt(brief: MusicBrief, platform: str = "generic") -> CompiledPrompt:
    """把统一 Brief 编译为平台适配的英文 Prompt，不依赖外部 LLM。"""
    parts = [brief.genre, brief.mood]
    if brief.use_case:
        parts.append(f"for {brief.use_case}")
    if brief.bpm:
        parts.append(f"{brief.bpm} BPM")
    if brief.key:
        parts.append(f"key: {brief.key}")
    if brief.vocals:
        parts.append(brief.vocals)
    if brief.language and brief.vocals != "instrumental":
        parts.append(f"{brief.language} lyrics")
    parts.extend(brief.instruments)
    parts.extend(brief.production)
    if brief.extra:
        parts.append(f"creative direction: {brief.extra}")

    # 平台适配保持独立：当前只改变输出组织，不虚构平台能力。
    if platform == "suno":
        style_prompt = ", ".join(parts)
    elif platform == "udio":
        style_prompt = ", ".join(parts)
    elif platform == "generic":
        style_prompt = ", ".join(parts)
    else:
        raise ValueError(f"不支持的平台: {platform}")

    structure = " → ".join(brief.structure) if brief.structure else ""
    return CompiledPrompt(
        platform=platform,
        brief=brief,
        style_prompt=style_prompt,
        negative_prompt=", ".join(brief.avoid),
        structure_prompt=structure,
        warnings=_warnings(brief),
    )


def remix_brief(brief: MusicBrief, **changes: Any) -> MusicBrief:
    """局部修改：未传入的字段原样保留。"""
    return MusicBrief.model_validate({**brief.model_dump(), **changes})


def diff_briefs(before: MusicBrief, after: MusicBrief) -> Dict[str, Dict[str, Any]]:
    before_data = before.model_dump()
    after_data = after.model_dump()
    return {
        key: {"before": before_data[key], "after": after_data[key]}
        for key in before_data
        if before_data[key] != after_data[key]
    }
