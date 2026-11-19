import json
import tempfile
import unittest
from pathlib import Path

from src.models.v2 import (
    GenerationEvaluation,
    MusicPromptV2,
    ParameterOrigin,
    extract_explicit_bpm,
    extract_explicit_key,
)
from src.repository import load_prompts, save_prompts, summarize


class ParameterExtractionTests(unittest.TestCase):
    def test_extracts_explicit_bpm_formats(self):
        self.assertEqual(extract_explicit_bpm("dark blues at 65 BPM"), 65)
        self.assertEqual(extract_explicit_bpm("BPM: 140, cowbell"), 140)
        self.assertEqual(extract_explicit_bpm("tempo=96"), 96)

    def test_rejects_missing_or_out_of_range_bpm(self):
        self.assertIsNone(extract_explicit_bpm("mid tempo"))
        self.assertIsNone(extract_explicit_bpm("999 BPM"))

    def test_extracts_only_explicit_key(self):
        self.assertEqual(extract_explicit_key("F minor, distorted bass"), "F minor")
        self.assertEqual(extract_explicit_key("key: C# Major"), "C# major")
        self.assertIsNone(extract_explicit_key("minor key, sad"))


class MusicPromptV2Tests(unittest.TestCase):
    def legacy(self):
        return {
            "id": "mp_test",
            "title": "Test Song",
            "prompt_text": "indie pop, 96 BPM, F minor, piano",
            "prompt_zh": "独立流行，钢琴",
            "platform": "suno",
            "genre": ["pop", "pop", "indie"],
            "quality_score": 8.2,
            "source": "community/post-1",
        }

    def test_legacy_migration_preserves_data_and_marks_explicit(self):
        prompt = MusicPromptV2.from_legacy(self.legacy())
        self.assertEqual(prompt.bpm, 96)
        self.assertEqual(prompt.bpm_origin, ParameterOrigin.EXPLICIT)
        self.assertEqual(prompt.key_signature, "F minor")
        self.assertEqual(prompt.genres, ["pop", "indie"])
        self.assertEqual(prompt.to_legacy()["prompt_text"], self.legacy()["prompt_text"])

    def test_missing_parameter_remains_unknown(self):
        data = self.legacy()
        data["prompt_text"] = "ambient piano"
        prompt = MusicPromptV2.from_legacy(data)
        self.assertIsNone(prompt.bpm)
        self.assertEqual(prompt.bpm_origin, ParameterOrigin.UNKNOWN)

    def test_inferred_origin_is_preserved(self):
        prompt = MusicPromptV2(
            id="inferred", title="Inferred", style_prompt="ambient",
            bpm=70, bpm_origin="inferred",
        )
        self.assertEqual(prompt.bpm_origin, ParameterOrigin.INFERRED)

    def test_verified_requires_evaluation(self):
        with self.assertRaises(ValueError):
            MusicPromptV2(
                id="bad", title="Bad", style_prompt="pop", verification_status="verified"
            )

    def test_generation_score_is_separate_from_text_score(self):
        prompt = MusicPromptV2(
            id="scored", title="Scored", style_prompt="pop", text_quality_score=9,
            verification_status="verified",
            evaluations=[
                GenerationEvaluation(platform="suno", generation_score=7),
                GenerationEvaluation(platform="suno", generation_score=9),
            ],
        )
        self.assertEqual(prompt.text_quality_score, 9)
        self.assertEqual(prompt.generation_score, 8)

    def test_jsonl_round_trip_and_duplicate_detection(self):
        prompt = MusicPromptV2.from_legacy(self.legacy())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompts.jsonl"
            save_prompts(path, [prompt])
            loaded = load_prompts(path)
            self.assertEqual(loaded[0].id, prompt.id)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(prompt.model_dump_json() + "\n")
            with self.assertRaisesRegex(ValueError, "重复 ID"):
                load_prompts(path)

    def test_summary_separates_curated_from_verified(self):
        prompt = MusicPromptV2.from_legacy(self.legacy())
        stats = summarize([prompt])
        self.assertEqual(stats["curated_prompts"], 1)
        self.assertEqual(stats["verified_prompts"], 0)


if __name__ == "__main__":
    unittest.main()
