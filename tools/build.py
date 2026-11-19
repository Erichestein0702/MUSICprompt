#!/usr/bin/env python3
"""从 v2 JSONL 统一构建 SQLite、CSV、网站数据与 README 统计。"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models import MusicPromptDB
from src.repository import load_prompts, summarize

ROOT = Path(__file__).parent.parent
START = "<!-- AUTO_STATS:START -->"
END = "<!-- AUTO_STATS:END -->"


def _write_csv(path, prompts):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id", "title", "title_zh", "style_prompt", "style_prompt_zh",
        "target_platform", "target_model", "genres", "instruments", "moods",
        "use_cases", "bpm", "bpm_origin", "key_signature", "key_origin",
        "text_quality_score", "generation_score", "verification_status",
        "source_url", "source_license",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for prompt in prompts:
            data = prompt.model_dump()
            row = {key: data.get(key) for key in fields}
            for key in ("genres", "instruments", "moods", "use_cases"):
                row[key] = "|".join(row[key])
            row["generation_score"] = prompt.generation_score
            row["source_url"] = prompt.source.url
            row["source_license"] = prompt.source.license
            writer.writerow(row)


def _stats_markdown(stats):
    return "\n".join([
        START,
        "| 指标 | 当前值 |",
        "|---|---:|",
        f"| 不重复 Prompt | {stats['total_prompts']} |",
        f"| 文本质量分 ≥ 8 | {stats['curated_prompts']} |",
        f"| 有明确 BPM | {stats['with_bpm']} |",
        f"| 有明确调性 | {stats['with_key']} |",
        f"| 已完成生成验证 | {stats['verified_prompts']} |",
        f"| 平均文本质量分 | {stats['average_text_quality']} |",
        END,
    ])


def _update_readme(path, stats):
    content = path.read_text(encoding="utf-8")
    block = _stats_markdown(stats)
    if START not in content or END not in content:
        raise ValueError("README 缺少 AUTO_STATS 标记")
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: block,
        content,
        flags=re.S,
    )
    path.write_text(updated, encoding="utf-8")


def _build_database(path, prompts):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp.db")
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(temporary) + suffix)
        if candidate.exists():
            candidate.unlink()
    db = MusicPromptDB(str(temporary))
    try:
        db.init_db()
        for prompt in prompts:
            if not db.insert_prompt(prompt.to_legacy()):
                raise RuntimeError(f"导入数据库失败: {prompt.id}")
    finally:
        db.close()
    os.replace(temporary, path)


def check_local_links(root=ROOT):
    missing = []
    for relative in ("README.md", "prompts/README.md"):
        file_path = root / relative
        content = file_path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", content):
            target = target.strip().split()[0]
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            clean_target = target.split("#")[0]
            if clean_target and not (file_path.parent / clean_target).resolve().exists():
                missing.append(f"{relative}: {target}")
    return missing


def build(root=ROOT):
    prompts = load_prompts(root / "data/prompts_v2.jsonl")
    stats = summarize(prompts)
    (root / "data/summary.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    csv_dir = root / "data/final_output/csv"
    _write_csv(csv_dir / "all_prompts.csv", prompts)
    _write_csv(
        csv_dir / "curated_prompts.csv",
        [p for p in prompts if p.text_quality_score >= 8],
    )
    web_data = root / "web/data"
    web_data.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": stats,
        "prompts": [p.model_dump(mode="json") for p in prompts],
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (web_data / "prompts.json").write_text(serialized + "\n", encoding="utf-8")
    (web_data / "prompts.js").write_text(
        "window.MUSICPROMPT_DATA=" + serialized + ";\n", encoding="utf-8"
    )
    _update_readme(root / "README.md", stats)
    _build_database(root / "data/musicprompts.db", prompts)
    missing = check_local_links(root)
    if missing:
        raise RuntimeError("发现失效链接:\n" + "\n".join(missing))
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只校验数据和本地链接")
    args = parser.parse_args()
    if args.check:
        prompts = load_prompts(ROOT / "data/prompts_v2.jsonl")
        missing = check_local_links()
        if missing:
            raise SystemExit("失效链接:\n" + "\n".join(missing))
        print(json.dumps(summarize(prompts), ensure_ascii=False, indent=2))
        return
    stats = build()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
