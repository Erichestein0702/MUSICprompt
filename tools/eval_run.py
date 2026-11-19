#!/usr/bin/env python3
"""评测任务管理：列出任务、录入真实生成评测、汇总报告、回填 Prompt。

用法示例：

列任务：
    python tools/eval_run.py --list
    python tools/eval_run.py --list --status pending

看任务：
    python tools/eval_run.py --task EV001

录入一次真实生成评测（评分必须来自真实试听，不能编造）：
    python tools/eval_run.py --record --task EV001 --platform suno \\
        --model suno-v5 --audio https://example.com/demo.mp3 \\
        --score 8.2 \\
        --ratings '{"style_fidelity":9,"structure":8,"vocal":7,"audio_quality":8,"musicality":8}' \\
        --notes "副歌风格还原好，bridge 略偏"

汇总报告：
    python tools/eval_run.py --report

把评测结果回填到 prompts_v2.jsonl（更新 evaluations 与验证状态）：
    python tools/eval_run.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.eval import (
    EvalResult,
    derive_verification_status,
    load_eval_results,
    load_eval_tasks,
    save_eval_results,
)
from src.models.v2 import GenerationEvaluation, MusicPromptV2
from src.repository import load_prompts, save_prompts

ROOT = Path(__file__).parent.parent
TASKS_PATH = ROOT / "data/eval_tasks.jsonl"
RESULTS_PATH = ROOT / "data/eval_results.jsonl"
PROMPTS_PATH = ROOT / "data/prompts_v2.jsonl"


def _load_all():
    tasks = load_eval_tasks(TASKS_PATH)
    results = load_eval_results(RESULTS_PATH)
    return tasks, results


def _task_progress(tasks, results):
    by_task = defaultdict(list)
    for result in results:
        by_task[result.task_id].append(result)
    progress = {}
    for task in tasks:
        items = by_task.get(task.task_id, [])
        progress[task.task_id] = {
            "results": items,
            "count": len(items),
            "average": (
                round(sum(r.generation_score for r in items) / len(items), 2)
                if items
                else None
            ),
        }
    return progress


def cmd_list(status_filter=None):
    tasks, results = _load_all()
    progress = _task_progress(tasks, results)
    shown = 0
    for task in tasks:
        info = progress[task.task_id]
        done = info["count"] > 0
        status = "done" if done else "pending"
        if status_filter and status != status_filter:
            continue
        anchor = task.prompt_id or task.composer_input[:28] + "..."
        average = f"{info['average']}" if info["average"] is not None else "-"
        print(
            f"{task.task_id}  [{status:7s}]  评测{info['count']}次  均分{average:>5}"
            f"  {task.name}  ({anchor})"
        )
        shown += 1
    done_count = sum(1 for t in tasks if progress[t.task_id]["count"] > 0)
    print(f"\n共 {len(tasks)} 个任务，已完成 {done_count} 个，本次列出 {shown} 个。")


def cmd_task(task_id):
    tasks, results = _load_all()
    task = next((t for t in tasks if t.task_id == task_id), None)
    if task is None:
        raise SystemExit(f"未找到评测任务: {task_id}")
    print(json.dumps(task.model_dump(mode="json"), ensure_ascii=False, indent=2))
    related = [r for r in results if r.task_id == task_id]
    print(f"\n已有评测记录 {len(related)} 条：")
    for item in related:
        print(
            f"  - {item.platform}/{item.model_version or '?'}  "
            f"score={item.generation_score}  {item.audio_url or '(无音频链接)'}"
        )


def cmd_record(args):
    tasks, results = _load_all()
    if not any(t.task_id == args.task for t in tasks):
        raise SystemExit(f"未找到评测任务: {args.task}")
    ratings = json.loads(args.ratings) if args.ratings else {}
    result = EvalResult(
        task_id=args.task,
        platform=args.platform,
        model_version=args.model,
        audio_url=args.audio,
        generation_score=args.score,
        ratings=ratings,
        notes=args.notes or "",
        evaluator=args.evaluator,
    )
    results.append(result)
    save_eval_results(RESULTS_PATH, results)
    print(f"已记录评测 {args.task} -> {RESULTS_PATH}（当前共 {len(results)} 条）")


def cmd_report():
    tasks, results = _load_all()
    progress = _task_progress(tasks, results)
    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if progress[t.task_id]["count"] > 0)
    all_scores = [r.generation_score for r in results]
    print("## 评测进度")
    print(f"任务总数: {total_tasks}  已完成: {done_tasks}  待评测: {total_tasks - done_tasks}")
    print(f"评测记录: {len(results)} 条")
    if all_scores:
        print(f"平均生成分: {round(sum(all_scores) / len(all_scores), 2)}")
    else:
        print("平均生成分: 暂无（尚无真实评测记录）")
    by_platform = defaultdict(list)
    for result in results:
        by_platform[result.platform].append(result.generation_score)
    if by_platform:
        print("\n## 按平台")
        for platform, scores in sorted(by_platform.items()):
            print(f"{platform}: {len(scores)} 条，均分 {round(sum(scores)/len(scores), 2)}")
    ranked = sorted(
        ((t.task_id, t.name, progress[t.task_id]["average"]) for t in tasks if progress[t.task_id]["average"] is not None),
        key=lambda item: -item[2],
    )
    if ranked:
        print("\n## 任务均分排行")
        for task_id, name, average in ranked[:5]:
            print(f"{task_id} {name}: {average}")
        print("...")
        for task_id, name, average in ranked[-3:]:
            print(f"{task_id} {name}: {average}")


def cmd_apply():
    tasks, results = _load_all()
    prompts = load_prompts(PROMPTS_PATH)
    by_prompt = defaultdict(list)
    task_map = {t.task_id: t for t in tasks}
    for result in results:
        task = task_map.get(result.task_id)
        if task and task.prompt_id:
            by_prompt[task.prompt_id].append(result)
    updated = 0
    new_prompts = []
    for prompt in prompts:
        related = by_prompt.get(prompt.id, [])
        if not related:
            new_prompts.append(prompt)
            continue
        evaluations = [
            GenerationEvaluation(
                platform=r.platform,
                model_version=r.model_version,
                audio_url=r.audio_url,
                generation_score=r.generation_score,
                ratings=r.ratings,
                notes=r.notes,
                evaluated_at=r.evaluated_at,
            )
            for r in related
        ]
        status = derive_verification_status(related)
        data = prompt.model_dump()
        data["evaluations"] = evaluations
        data["verification_status"] = status
        new_prompts.append(MusicPromptV2.model_validate(data))
        updated += 1
    save_prompts(PROMPTS_PATH, new_prompts)
    print(f"已回填 {updated} 条 Prompt 的评测记录 -> {PROMPTS_PATH}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="列出评测任务")
    parser.add_argument("--status", choices=["pending", "done"], help="按状态过滤")
    parser.add_argument("--task", help="查看或录指定任务")
    parser.add_argument("--record", action="store_true", help="录入一次真实生成评测")
    parser.add_argument("--platform", help="生成平台")
    parser.add_argument("--model", help="模型版本")
    parser.add_argument("--audio", help="生成结果音频链接")
    parser.add_argument("--score", type=float, help="总体生成分 0-10")
    parser.add_argument("--ratings", help="维度评分 JSON")
    parser.add_argument("--notes", help="备注")
    parser.add_argument("--evaluator", default="human", help="评测者")
    parser.add_argument("--report", action="store_true", help="汇总报告")
    parser.add_argument("--apply", action="store_true", help="回填评测结果到 Prompt")
    args = parser.parse_args()

    if args.record:
        if not (args.task and args.platform and args.score is not None):
            raise SystemExit("--record 需要 --task --platform --score")
        cmd_record(args)
    elif args.list:
        cmd_list(args.status)
    elif args.task and not args.record:
        cmd_task(args.task)
    elif args.report:
        cmd_report()
    elif args.apply:
        cmd_apply()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
