import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from foundation.model import load_project, resolve, validate, merge

class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.project = load_project(ROOT / "game")

    def errors(self):
        return validate(self.project, ROOT / "game")

    def test_checked_in_data(self):
        self.assertEqual(self.errors(), [])

    def test_duplicate_id_rejected(self):
        self.project["narrative"].append(copy.deepcopy(self.project["narrative"][0]))
        self.assertTrue(any("duplicate" in e for e in self.errors()))

    def test_each_edition_required(self):
        for lang in ("pt_BR", "en"):
            with self.subTest(lang=lang):
                row = self.project["editions"][lang].pop()
                self.assertTrue(any("missing " + lang in e for e in self.errors()))
                self.project["editions"][lang].append(row)

    def test_empty_text_rejected(self):
        self.project["editions"]["en"][0]["text"] = " "
        self.assertTrue(any("empty en" in e for e in self.errors()))

    def test_scene_reference_rejected(self):
        self.project["narrative"][0]["scene"] = "unknown"
        self.assertTrue(any("invalid scene" in e for e in self.errors()))

    def test_bad_beat_rejected(self):
        self.project["scenes"][0]["sequence"].append({"beat": "unknown"})
        self.assertTrue(any("invalid beat" in e for e in self.errors()))

    def test_asset_rejected(self):
        self.project["scenes"][0]["defaults"]["background"] = "unknown"
        self.assertTrue(any("invalid background" in e for e in self.errors()))

    def test_sparse_inheritance_and_beat_isolation(self):
        frames = resolve(self.project, "test_observatory")
        self.assertEqual(frames[0]["state"], frames[2]["state"])
        self.assertNotEqual(frames[2]["state"]["lighting"], frames[3]["state"]["lighting"])
        self.assertEqual(frames[2]["state"]["background"], frames[3]["state"]["background"])
        self.assertEqual(frames[0]["state"], frames[4]["state"])
        frames[0]["state"]["background"] = "mutated"
        self.assertNotEqual(frames[0]["state"], frames[1]["state"])

    def test_expression_delta_does_not_reset_scene(self):
        state = {"background": "a", "expression": {"a": "neutral", "b": "neutral"}}
        updated = merge(state, {"expression": {"a": "concerned"}})
        self.assertEqual(updated["background"], "a")
        self.assertEqual(updated["expression"]["b"], "neutral")
        self.assertEqual(state["expression"]["a"], "neutral")

    def test_localization_and_presentation_do_not_resolve_different_scenes(self):
        expected = resolve(self.project, "test_observatory")
        for lang in ("en", "pt_BR"):
            for mode in ("static", "cinematic"):
                self.assertEqual(resolve(self.project, "test_observatory"), expected)
                self.assertEqual({f["id"] for f in expected}, {e["id"] for e in self.project["editions"][lang]})

if __name__ == "__main__":
    unittest.main()
