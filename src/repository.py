"""JSONL 事实数据的读写、校验与统计。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.models.v2 import MusicPromptV2


def load_prompts(path: Path) -> List[MusicPromptV2]:
    prompts: List[MusicPromptV2] = []
    ids = set()
    prompts_text = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                prompt = MusicPromptV2.model_validate_json(line)
            except Exception as exc:
                raise ValueError(f"{path}:{line_number} 数据无效: {exc}") from exc
            if prompt.id in ids:
                raise ValueError(f"重复 ID: {prompt.id}")
            normalized_text = " ".join(prompt.style_prompt.casefold().split())
            if normalized_text in prompts_text:
                raise ValueError(f"重复 Prompt 文本: {prompt.id}")
            ids.add(prompt.id)
            prompts_text.add(normalized_text)
            prompts.append(prompt)
    return sorted(prompts, key=lambda item: item.id)


def save_prompts(path: Path, prompts: Iterable[MusicPromptV2]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for prompt in sorted(prompts, key=lambda item: item.id):
            handle.write(prompt.model_dump_json() + "\n")


def summarize(prompts: Iterable[MusicPromptV2], eval_tasks=None, eval_results=None) -> Dict[str, Any]:
    items = list(prompts)
    genres = Counter(g for item in items for g in item.genres)
    platforms = Counter(item.target_platform for item in items)
    curated = sum(
        item.generation_score is not None and item.generation_score >= 8
        for item in items
    )
    generation_scores = [
        item.generation_score for item in items if item.generation_score is not None
    ]
    stats: Dict[str, Any] = {
        "schema_version": "2.0.0",
        "total_prompts": len(items),
        "curated_prompts": curated,
        "text_quality_curated": sum(item.text_quality_score >= 8 for item in items),
        "verified_prompts": sum(item.verification_status.value == "verified" for item in items),
        "with_bpm": sum(item.bpm is not None for item in items),
        "with_key": sum(item.key_signature is not None for item in items),
        "average_text_quality": round(
            sum(item.text_quality_score for item in items) / len(items), 2
        ) if items else 0,
        "average_generation_score": round(
            sum(generation_scores) / len(generation_scores), 2
        ) if generation_scores else None,
        "genres": dict(genres.most_common()),
        "platforms": dict(platforms.most_common()),
    }
    if eval_tasks is not None:
        done_ids = {item.task_id for item in (eval_results or [])}
        stats["eval_tasks_total"] = len(eval_tasks)
        stats["eval_tasks_done"] = sum(
            task.task_id in done_ids for task in eval_tasks
        )
        stats["eval_results_total"] = len(eval_results or [])
    return stats
