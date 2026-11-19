#!/usr/bin/env python3
"""将现有 v1 SQLite 数据库迁移为可审查的 v2 JSONL 事实数据。"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.v2 import MusicPromptV2
from src.repository import save_prompts, summarize


def migrate(db_path: Path, output: Path, force: bool = False):
    if output.exists() and not force:
        raise FileExistsError(f"{output} 已存在；如需覆盖请使用 --force")
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT * FROM prompts ORDER BY id").fetchall()
    prompts = []
    for row in rows:
        legacy = dict(row)
        legacy["genre"] = [
            r[0] for r in connection.execute(
                """SELECT g.name FROM genres g
                   JOIN prompt_genres pg ON pg.genre_id=g.id
                   WHERE pg.prompt_id=? ORDER BY g.name""",
                (legacy["id"],),
            )
        ]
        legacy["instruments"] = [
            r[0] for r in connection.execute(
                """SELECT i.name FROM instruments i
                   JOIN prompt_instruments pi ON pi.instrument_id=i.id
                   WHERE pi.prompt_id=? ORDER BY i.name""",
                (legacy["id"],),
            )
        ]
        legacy["use_cases"] = [
            r[0] for r in connection.execute(
                """SELECT u.name FROM use_cases u
                   JOIN prompt_use_cases pu ON pu.use_case_id=u.id
                   WHERE pu.prompt_id=? ORDER BY u.name""",
                (legacy["id"],),
            )
        ]
        legacy["moods"] = [
            r[0] for r in connection.execute(
                """SELECT m.name FROM moods m
                   JOIN prompt_moods pm ON pm.mood_id=m.id
                   WHERE pm.prompt_id=? ORDER BY m.name""",
                (legacy["id"],),
            )
        ]
        prompts.append(MusicPromptV2.from_legacy(legacy))
    connection.close()
    save_prompts(output, prompts)
    return prompts


def main():
    root = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=root / "data/musicprompts.db")
    parser.add_argument("--output", type=Path, default=root / "data/prompts_v2.jsonl")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    prompts = migrate(args.db, args.output, args.force)
    print(f"已迁移 {len(prompts)} 条记录到 {args.output}")
    print(summarize(prompts))


if __name__ == "__main__":
    main()
