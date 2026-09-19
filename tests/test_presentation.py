import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))

from foundation.model import (
    LANGUAGES,
    PRESENTATION_KINDS,
    load_project,
    presentation_for,
    presentation_segment,
    resolve_presentation_text,
    validate,
)


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.project = load_project(ROOT / "game")

    def errors(self):
        return validate(self.project, ROOT / "game")

    def first_explicit(self):
        return self.project["presentation_groups"][0]["segments"]

    def test_real_prologue_has_explicit_presentation_and_full_coverage(self):
        expected = {f"arc01.prologue.{number:04d}" for number in range(1, 7)}
        self.assertEqual(set(self.project["presentation_by_narrative"]), expected)
        segment_ids = []
        for narrative_id in sorted(expected):
            segments = presentation_for(self.project, narrative_id)
            segment_ids.extend(segment["id"] for segment in segments)
            for language in LANGUAGES:
                text = self.project["presentation_translation_by_language"][language][narrative_id]["text"]
                reconstructed = "".join(
                    resolve_presentation_text(self.project, narrative_id, segment["id"], language)
                    for segment in segments
                )
                self.assertEqual(reconstructed, text)
                self.assertTrue(all(
                    resolve_presentation_text(self.project, narrative_id, segment["id"], language, display=True)
                    for segment in segments
                ))
        self.assertEqual(len(segment_ids), len(set(segment_ids)))
        self.assertEqual(self.errors(), [])

    def test_shared_segment_resolves_independent_language_ranges(self):
        narrative_id = "arc01.prologue.0001"
        segment_id = narrative_id + ".p001"
        pt_text = resolve_presentation_text(self.project, narrative_id, segment_id, "pt_BR")
        en_text = resolve_presentation_text(self.project, narrative_id, segment_id, "en")
        self.assertNotEqual(pt_text, en_text)
        self.assertEqual(presentation_segment(self.project, narrative_id, segment_id)["ordinal"], 0)

    def test_old_content_gets_transient_whole_translation_fallback(self):
        narrative_id = "test.ch01.observatory.0001"
        segments = presentation_for(self.project, narrative_id)
        self.assertEqual(len(segments), 1)
        self.assertTrue(segments[0]["synthetic"])
        self.assertEqual(segments[0]["kind"], self.project["narrative_by_id"][narrative_id]["kind"])
        for language in LANGUAGES:
            self.assertEqual(
                resolve_presentation_text(self.project, narrative_id, segments[0]["id"], language),
                self.project["presentation_translation_by_language"][language][narrative_id]["text"],
            )

    def test_display_trim_does_not_mutate_source_translation(self):
        narrative_id = "arc01.prologue.0002"
        segment_id = narrative_id + ".p001"
        source = self.project["presentation_translation_by_language"]["pt_BR"][narrative_id]["text"]
        raw = resolve_presentation_text(self.project, narrative_id, segment_id, "pt_BR")
        display = resolve_presentation_text(self.project, narrative_id, segment_id, "pt_BR", display=True)
        self.assertNotEqual(raw, display)
        self.assertEqual(source, self.project["presentation_translation_by_language"]["pt_BR"][narrative_id]["text"])

    def test_gap_and_incomplete_coverage_are_rejected(self):
        self.first_explicit()[0]["ranges"]["en"]["start"] = 1
        errors = self.errors()
        self.assertTrue(any("gap in en presentation" in error for error in errors))

    def test_overlap_and_order_are_rejected(self):
        self.first_explicit()[1]["ranges"]["pt_BR"]["start"] -= 1
        self.assertTrue(any("overlapping pt_BR presentation" in error for error in self.errors()))

    def test_out_of_range_and_missing_language_are_rejected(self):
        segment = self.first_explicit()[0]
        original = copy.deepcopy(segment["ranges"]["en"])
        segment["ranges"]["en"]["end"] = 10**9
        self.assertTrue(any("invalid en presentation range" in error for error in self.errors()))
        segment["ranges"]["en"] = original
        segment["ranges"].pop("en")
        self.assertTrue(any("missing en presentation range" in error for error in self.errors()))

    def test_duplicate_segment_ids_are_rejected_globally(self):
        groups = self.project["presentation_groups"]
        groups[1]["segments"][0]["id"] = groups[0]["segments"][0]["id"]
        self.assertTrue(any("duplicate/empty presentation segment ID" in error for error in self.errors()))

    def test_invalid_kind_and_speaker_are_rejected(self):
        segment = self.first_explicit()[0]
        segment["kind"] = "aside"
        segment["speaker"] = "future.character"
        errors = self.errors()
        self.assertTrue(any("invalid presentation kind" in error for error in errors))
        self.assertTrue(any("invalid presentation speaker" in error for error in errors))
        self.assertNotIn("aside", PRESENTATION_KINDS)

    def test_unknown_parent_and_missing_required_parent_are_rejected(self):
        group = self.project["presentation_groups"][0]
        original = group["parent_id"]
        group["parent_id"] = "unknown.parent"
        errors = self.errors()
        self.assertIn("unknown presentation parent: unknown.parent", errors)
        self.assertIn("missing explicit presentation: " + original, errors)


if __name__ == "__main__":
    unittest.main()
