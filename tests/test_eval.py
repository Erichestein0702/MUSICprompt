"""评测闭环回归测试。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.models.eval import (
    EvalResult,
    EvalTask,
    derive_verification_status,
    load_eval_results,
    load_eval_tasks,
    save_eval_results,
)
from src.repository import load_prompts, summarize

import tools.eval_run as eval_run


def _make_result(task_id="EV001", score=8.5, platform="suno"):
    return EvalResult(
        task_id=task_id,
        platform=platform,
        model_version="v5",
        audio_url="https://example.com/a.mp3",
        generation_score=score,
        ratings={"style_fidelity": 8, "structure": 8},
        notes="ok",
    )


class TestEvalModels(unittest.TestCase):
    def test_task_requires_anchor(self):
        with self.assertRaises(Exception):
            EvalTask(task_id="X", name="n", brief="b")

    def test_task_accepts_prompt_anchor(self):
        task = EvalTask(task_id="X", name="n", brief="b", prompt_id="mp_1")
        self.assertEqual(task.prompt_id, "mp_1")

    def test_task_accepts_composer_anchor(self):
        task = EvalTask(task_id="X", name="n", brief="b", composer_input="做一首歌")
        self.assertEqual(task.composer_input, "做一首歌")

    def test_result_score_range(self):
        with self.assertRaises(Exception):
            EvalResult(task_id="X", platform="suno", generation_score=11)

    def test_result_ratings_range(self):
        with self.assertRaises(Exception):
            EvalResult(
                task_id="X", platform="suno", generation_score=5,
                ratings={"style": 12},
            )


class TestVerificationStatus(unittest.TestCase):
    def test_empty_is_unverified(self):
        self.assertEqual(derive_verification_status([]), "unverified")

    def test_low_score_is_tested(self):
        results = [_make_result(score=6.5)]
        self.assertEqual(derive_verification_status(results), "tested")

    def test_high_score_is_verified(self):
        results = [_make_result(score=8.0), _make_result(score=9.0)]
        self.assertEqual(derive_verification_status(results), "verified")

    def test_average_below_threshold_is_tested(self):
        results = [_make_result(score=9.0), _make_result(score=6.0)]
        self.assertEqual(derive_verification_status(results), "tested")


class TestTaskCorpus(unittest.TestCase):
    def test_corpus_shape(self):
        tasks = load_eval_tasks(ROOT / "data/eval_tasks.jsonl")
        self.assertEqual(len(tasks), 40)
        ids = [t.task_id for t in tasks]
        self.assertEqual(len(ids), len(set(ids)))
        fixed = [t for t in tasks if t.prompt_id]
        composed = [t for t in tasks if t.composer_input]
        self.assertEqual(len(fixed), 12)
        self.assertEqual(len(composed), 28)

    def test_prompt_refs_exist(self):
        tasks = load_eval_tasks(ROOT / "data/eval_tasks.jsonl")
        prompt_ids = {p.id for p in load_prompts(ROOT / "data/prompts_v2.jsonl")}
        for task in tasks:
            if task.prompt_id:
                self.assertIn(task.prompt_id, prompt_ids)

    def test_every_task_has_expected(self):
        tasks = load_eval_tasks(ROOT / "data/eval_tasks.jsonl")
        for task in tasks:
            self.assertTrue(task.expected, f"{task.task_id} 缺少验收点")


class TestEvalWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self._saved = {
            "TASKS_PATH": eval_run.TASKS_PATH,
            "RESULTS_PATH": eval_run.RESULTS_PATH,
            "PROMPTS_PATH": eval_run.PROMPTS_PATH,
        }
        eval_run.TASKS_PATH = self.dir / "eval_tasks.jsonl"
        eval_run.RESULTS_PATH = self.dir / "eval_results.jsonl"
        eval_run.PROMPTS_PATH = self.dir / "prompts_v2.jsonl"

    def tearDown(self):
        for key, value in self._saved.items():
            setattr(eval_run, key, value)
        self.tmp.cleanup()

    def _write_fixture(self):
        task = EvalTask(task_id="EV001", name="t", brief="b", prompt_id="mp_1")
        eval_run.TASKS_PATH.write_text(task.model_dump_json() + "\n", encoding="utf-8")
        prompt = {
            "id": "mp_1",
            "title": "Demo",
            "style_prompt": "demo prompt",
            "text_quality_score": 9.0,
            "verification_status": "unverified",
        }
        eval_run.PROMPTS_PATH.write_text(
            json.dumps(prompt, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def test_record_persists_result(self):
        self._write_fixture()
        args = type("Args", (), {
            "task": "EV001", "platform": "suno", "model": "v5",
            "audio": "https://example.com/a.mp3", "score": 8.2,
            "ratings": '{"style_fidelity": 9}', "notes": "good",
            "evaluator": "human",
        })()
        eval_run.cmd_record(args)
        results = load_eval_results(eval_run.RESULTS_PATH)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].generation_score, 8.2)

    def test_record_rejects_unknown_task(self):
        self._write_fixture()
        args = type("Args", (), {
            "task": "EV999", "platform": "suno", "model": None,
            "audio": None, "score": 8.0,
            "ratings": None, "notes": "", "evaluator": "human",
        })()
        with self.assertRaises(SystemExit):
            eval_run.cmd_record(args)

    def test_apply_updates_verification(self):
        self._write_fixture()
        save_eval_results(eval_run.RESULTS_PATH, [_make_result(score=8.6)])
        eval_run.cmd_apply()
        prompts = load_prompts(eval_run.PROMPTS_PATH)
        self.assertEqual(prompts[0].verification_status.value, "verified")
        self.assertEqual(len(prompts[0].evaluations), 1)

    def test_apply_keeps_unverified_without_results(self):
        self._write_fixture()
        eval_run.cmd_apply()
        prompts = load_prompts(eval_run.PROMPTS_PATH)
        self.assertEqual(prompts[0].verification_status.value, "unverified")


class TestSummary(unittest.TestCase):
    def test_curated_driven_by_generation_score(self):
        prompt_high_text = {
            "id": "a", "title": "A", "style_prompt": "aaa",
            "text_quality_score": 9.0, "verification_status": "unverified",
        }
        prompt_verified = {
            "id": "b", "title": "B", "style_prompt": "bbb",
            "text_quality_score": 5.0, "verification_status": "verified",
            "evaluations": [{
                "platform": "suno", "generation_score": 8.5,
                "ratings": {}, "notes": "",
            }],
        }
        prompts = [
            __import__("src.models.v2", fromlist=["MusicPromptV2"]).MusicPromptV2.model_validate(prompt_high_text),
            __import__("src.models.v2", fromlist=["MusicPromptV2"]).MusicPromptV2.model_validate(prompt_verified),
        ]
        tasks = [EvalTask(task_id="EV001", name="t", brief="b", prompt_id="a")]
        results = [_make_result(score=8.5)]
        stats = summarize(prompts, tasks, results)
        # 文本分高的不进精选，生成分高的进精选
        self.assertEqual(stats["curated_prompts"], 1)
        self.assertEqual(stats["text_quality_curated"], 1)
        self.assertEqual(stats["eval_tasks_total"], 1)
        self.assertEqual(stats["eval_tasks_done"], 1)
        self.assertEqual(stats["eval_results_total"], 1)


if __name__ == "__main__":
    unittest.main()
