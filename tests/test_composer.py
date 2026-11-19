import unittest

from src.composer import (
    MusicBrief, brief_from_text, compile_prompt, diff_briefs, remix_brief,
)


class ComposerTests(unittest.TestCase):
    def test_parses_chinese_brief(self):
        brief = brief_from_text(
            "雨夜开车，克制的中文独立流行，96 BPM，F 小调，钢琴和合成器，女声"
        )
        self.assertEqual(brief.genre, "indie pop")
        self.assertEqual(brief.bpm, 96)
        self.assertEqual(brief.key, "F minor")
        self.assertEqual(brief.vocals, "female vocals")
        self.assertIn("piano", brief.instruments)
        self.assertIn("synthesizer", brief.instruments)
        self.assertEqual(brief.language, "Chinese")

    def test_compiles_explicit_parameters_and_original_intent(self):
        brief = MusicBrief(
            genre="indie pop", mood="restrained", bpm=96, key="F minor",
            vocals="female vocals", instruments=["piano"],
            structure=["intro", "verse", "chorus"], avoid=["EDM drop"],
        )
        result = compile_prompt(brief, "suno")
        self.assertIn("96 BPM", result.style_prompt)
        self.assertIn("F minor", result.style_prompt)
        self.assertEqual(result.negative_prompt, "EDM drop")
        self.assertEqual(result.structure_prompt, "intro → verse → chorus")

    def test_does_not_invent_bpm(self):
        result = compile_prompt(MusicBrief(genre="ambient", mood="calm"))
        self.assertNotIn("BPM", result.style_prompt)

    def test_remix_preserves_untouched_fields(self):
        original = MusicBrief(genre="folk", mood="warm", bpm=72, instruments=["guitar"])
        changed = remix_brief(original, bpm=82)
        self.assertEqual(changed.genre, "folk")
        self.assertEqual(changed.instruments, ["guitar"])
        self.assertEqual(diff_briefs(original, changed), {"bpm": {"before": 72, "after": 82}})

    def test_warns_about_instrumental_language_conflict(self):
        brief = MusicBrief(vocals="instrumental", language="Chinese")
        self.assertTrue(compile_prompt(brief).warnings)

    def test_rejects_unknown_platform(self):
        with self.assertRaises(ValueError):
            compile_prompt(MusicBrief(), "unknown")


if __name__ == "__main__":
    unittest.main()
