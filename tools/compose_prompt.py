#!/usr/bin/env python3
"""从自然语言或 JSON Brief 生成、局部修改并比较音乐 Prompt。"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.composer import (
    MusicBrief, brief_from_text, compile_prompt, diff_briefs, remix_brief,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="一句话音乐需求")
    source.add_argument("--brief", type=Path, help="MusicBrief JSON 文件")
    parser.add_argument("--platform", choices=["generic", "suno", "udio"], default="generic")
    parser.add_argument("--set", dest="changes", help="局部修改 JSON，如 '{\"bpm\": 100}'")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON")
    args = parser.parse_args()

    brief = (
        MusicBrief.model_validate_json(args.brief.read_text(encoding="utf-8"))
        if args.brief else brief_from_text(args.text)
    )
    original = brief
    if args.changes:
        changes = json.loads(args.changes)
        if not isinstance(changes, dict):
            raise SystemExit("--set 必须是 JSON 对象")
        brief = remix_brief(brief, **changes)
    compiled = compile_prompt(brief, args.platform)
    if args.json:
        output = compiled.model_dump(mode="json")
        if args.changes:
            output["diff"] = diff_briefs(original, brief)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return
    print("Style Prompt:\n" + compiled.style_prompt)
    if compiled.negative_prompt:
        print("\nNegative Prompt:\n" + compiled.negative_prompt)
    if compiled.structure_prompt:
        print("\nStructure:\n" + compiled.structure_prompt)
    for warning in compiled.warnings:
        print("\nWarning: " + warning)
    if args.changes:
        print("\nChanges:\n" + json.dumps(diff_briefs(original, brief), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
