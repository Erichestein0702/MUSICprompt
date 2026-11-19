"""评测任务与评测结果数据模型。

评测结果必须来自真实生成评测（人工盲听或约定评分流程），
不允许用文本质量分推导，也不允许伪造音频链接或评分。
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EVAL_DIMENSIONS: List[str] = [
    "style_fidelity",
    "structure",
    "vocal",
    "audio_quality",
    "musicality",
]

VERIFIED_THRESHOLD = 8.0


class EvalTaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class EvalTask(BaseModel):
    """一条固定评测任务。任务本身是测试用例设计，不包含生成结果。"""

    task_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    prompt_id: Optional[str] = None
    composer_input: Optional[str] = None
    target_platforms: List[str] = Field(default_factory=lambda: ["suno", "udio"])
    expected: Dict[str, str] = Field(default_factory=dict)
    dimensions: List[str] = Field(default_factory=lambda: list(EVAL_DIMENSIONS))
    tags: List[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def normalize_task_id(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_task_anchor(self) -> "EvalTask":
        if not self.prompt_id and not self.composer_input:
            raise ValueError("评测任务必须提供 prompt_id 或 composer_input 之一")
        return self


class EvalResult(BaseModel):
    """一次真实生成评测记录。"""

    task_id: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    model_version: Optional[str] = None
    audio_url: Optional[str] = None
    generation_score: float = Field(ge=0, le=10)
    ratings: Dict[str, float] = Field(default_factory=dict)
    notes: str = ""
    evaluator: str = "human"
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


def derive_verification_status(
    evaluations: List[EvalResult],
) -> str:
    """由真实评测结果推导验证状态。

    - 无评测 -> unverified
    - 有评测但平均生成分低于阈值 -> tested
    - 平均生成分达到阈值 -> verified
    """
    if not evaluations:
        return "unverified"
    scores = [item.generation_score for item in evaluations]
    average = sum(scores) / len(scores)
    return "verified" if average >= VERIFIED_THRESHOLD else "tested"


def load_eval_tasks(path) -> List[EvalTask]:
    import json

    tasks: List[EvalTask] = []
    seen = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                task = EvalTask.model_validate_json(line)
            except Exception as exc:
                raise ValueError(f"{path}:{line_number} 评测任务无效: {exc}") from exc
            if task.task_id in seen:
                raise ValueError(f"重复评测任务 ID: {task.task_id}")
            seen.add(task.task_id)
            tasks.append(task)
    return sorted(tasks, key=lambda item: item.task_id)


def load_eval_results(path) -> List[EvalResult]:
    import json

    if not path.exists():
        return []
    results: List[EvalResult] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                result = EvalResult.model_validate_json(line)
            except Exception as exc:
                raise ValueError(f"{path}:{line_number} 评测结果无效: {exc}") from exc
            results.append(result)
    return results


def save_eval_results(path, results: List[EvalResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(result.model_dump_json() + "\n")
