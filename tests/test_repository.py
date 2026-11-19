import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.db.models import MusicPromptDB
from src.models.v2 import MusicPromptV2
from tools.build import check_local_links

ROOT = Path(__file__).parent.parent


class DatabaseV2Tests(unittest.TestCase):
    def test_v2_fields_round_trip_through_sqlite_and_fts(self):
        prompt = MusicPromptV2(
            id="mp_db", title="Database Song", style_prompt="ambient piano, 70 BPM",
            target_platform="suno", target_model="test-model", genres=["ambient"],
            bpm=70, bpm_origin="explicit", negative_prompt="drums",
        )
        with tempfile.TemporaryDirectory() as directory:
            db = MusicPromptDB(str(Path(directory) / "test.db"))
            try:
                db.init_db()
                self.assertTrue(db.insert_prompt(prompt.to_legacy()))
                row = db.get_all()[0]
                self.assertEqual(row["schema_version"], "2.0.0")
                self.assertEqual(row["target_model"], "test-model")
                self.assertEqual(row["negative_prompt"], "drums")
                self.assertEqual(db.search("ambient")[0]["id"], "mp_db")
            finally:
                db.close()


class RepositoryBuildTests(unittest.TestCase):
    def test_real_dataset_is_complete_and_deduplicated(self):
        lines = (ROOT / "data/prompts_v2.jsonl").read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line]
        self.assertEqual(len(records), 283)
        self.assertEqual(len({r["id"] for r in records}), 283)
        self.assertEqual(len({r["style_prompt"].casefold() for r in records}), 283)

    def test_build_exports_csv_and_web_data(self):
        with (ROOT / "data/final_output/csv/all_prompts.csv").open(encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 283)
        payload = json.loads((ROOT / "web/data/prompts.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["total_prompts"], 283)
        self.assertEqual(payload["summary"]["with_bpm"], 49)
        self.assertEqual(payload["summary"]["with_key"], 23)

    def test_primary_markdown_links_exist(self):
        self.assertEqual(check_local_links(ROOT), [])


if __name__ == "__main__":
    unittest.main()
