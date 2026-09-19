import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from foundation.model import advance_progress, canonical_furthest_id, chapter_for_narrative, load_project, memory_unlocks, presentation_for, resolve, resolve_presentation_direction, resolve_scene_visual_slots, unlocked_chapters, validate, merge

class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.project = load_project(ROOT / "game")

    def errors(self):
        return validate(self.project, ROOT / "game")

    def test_checked_in_data(self):
        self.assertEqual(self.errors(), [])

    def test_global_confirmation_renders_its_supplied_message(self):
        screen = (ROOT / "game/ui/main_menu/menu.rpy").read_text(encoding="utf-8")
        self.assertIn('text message id "confirm_message"', screen)

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
        expected_ids = set(self.project["narrative_order"])
        for lang in ("en", "pt_BR"):
            for mode in ("static", "cinematic"):
                resolved_ids = set()
                for scene in self.project["scenes"]:
                    resolved_ids.update(frame["id"] for frame in resolve(self.project, scene["id"]))
                self.assertEqual(resolved_ids, expected_ids)
                self.assertEqual(resolved_ids, {e["id"] for e in self.project["editions"][lang]})

    def test_chapter_order_and_unlocks_use_canonical_data(self):
        first, second = self.project["chapter_order"][1:]
        self.assertEqual(chapter_for_narrative(self.project, "test.ch02.rooftop.0001"), second)
        self.assertEqual(unlocked_chapters(self.project, -1), set())
        self.assertEqual(
            unlocked_chapters(self.project, self.project["narrative_index"]["test.ch01.observatory.0006"]),
            {"arc01.prologue", first},
        )
        self.assertEqual(
            unlocked_chapters(self.project, self.project["narrative_index"]["test.ch02.rooftop.0001"]),
            {"arc01.prologue", first, second},
        )

    def test_loaded_indexes_reconstruct_each_narrative_position(self):
        for narrative_id in self.project["narrative_order"]:
            scene_id = self.project["narrative_to_scene"][narrative_id]
            frame_index = self.project["frame_index_by_narrative"][narrative_id]
            self.assertEqual(self.project["frames_by_scene"][scene_id][frame_index]["id"], narrative_id)
            self.assertIn(self.project["narrative_to_chapter"][narrative_id], self.project["chapter_by_id"])

    def test_cached_scene_frames_match_resolved_scene_definition(self):
        for scene_id, frames in self.project["frames_by_scene"].items():
            self.assertEqual(frames, resolve(self.project, scene_id))

    def test_real_prologue_uses_final_scene_and_technical_asset_only(self):
        scene_id = "arc01.prologue.sc001"
        self.assertEqual(self.project["chapter_by_id"]["arc01.prologue"]["scenes"], [scene_id])
        self.assertEqual(
            {self.project["narrative_to_scene"][f"arc01.prologue.{number:04d}"] for number in range(1, 7)},
            {scene_id},
        )
        scene = self.project["scene_by_id"][scene_id]
        self.assertEqual(scene["defaults"]["background"], "bg.arc01.prologue.unknown_ground")
        self.assertNotIn("observatory", str(scene).lower())
        self.assertNotIn("test.", str(scene).lower())

    def test_every_real_presentation_resolves_complete_direction(self):
        expected_ids = {
            segment["id"]
            for number in range(1, 7)
            for segment in presentation_for(self.project, f"arc01.prologue.{number:04d}")
        }
        resolved_ids = set()
        for mode in ("static", "cinematic"):
            for number in range(1, 7):
                narrative_id = f"arc01.prologue.{number:04d}"
                for segment in presentation_for(self.project, narrative_id):
                    state = resolve_presentation_direction(self.project, narrative_id, segment["id"])
                    resolved_ids.add(segment["id"])
                    self.assertEqual(state["background"], "bg.arc01.prologue.unknown_ground", mode)
                    self.assertIn(state["composition_id"], self.project["art_requirement_by_id"], mode)
                    self.assertIn(state["shot"], {"low", "detail", "close"}, mode)
                    self.assertIn(state["animation"], {"none", "subtle"}, mode)
        self.assertEqual(resolved_ids, expected_ids)
        self.assertEqual(len(resolved_ids), 25)

    def test_production_visual_slots_resolve_with_development_fallbacks(self):
        planned = {
            "bg.arc01.prologue.unknown_ground",
            "comp.arc01.prologue.protagonist_down",
            "comp.arc01.prologue.black_boot",
            "comp.arc01.prologue.second_arrival",
            "comp.arc01.prologue.hand_contact",
            "cg.arc01.prologue.final_moment",
        }
        slots = {
            asset_id
            for kind in ("background", "composition", "hero_cg")
            for asset_id, entry in self.project["assets"].get(kind, {}).items()
            if isinstance(entry, dict) and entry.get("status") == "planned"
        }
        self.assertEqual(slots, planned)
        for number in range(1, 7):
            narrative_id = f"arc01.prologue.{number:04d}"
            for segment in presentation_for(self.project, narrative_id):
                state = resolve_presentation_direction(self.project, narrative_id, segment["id"])
                visual = resolve_scene_visual_slots(self.project, state)
                self.assertEqual(visual["background"]["id"], "bg.arc01.prologue.unknown_ground")
                self.assertEqual(visual["background"]["status"], "planned")
                self.assertIn(visual["foreground"]["id"], planned)
                self.assertEqual(visual["foreground"]["status"], "planned")
                self.assertTrue(visual["foreground"]["development_placeholder"])

    def test_legacy_scene_stays_background_only(self):
        state = resolve(self.project, "test_observatory")[0]["state"]
        visual = resolve_scene_visual_slots(self.project, state)
        self.assertEqual(visual["background"]["id"], "observatory")
        self.assertIsNone(visual["foreground"])

    def test_missing_production_slot_is_rejected(self):
        self.project["assets"]["composition"].pop("comp.arc01.prologue.black_boot")
        errors = self.errors()
        self.assertTrue(any("missing production asset slot: comp.arc01.prologue.black_boot" in error for error in errors))
        self.assertTrue(any("missing art production slot: comp.arc01.prologue.black_boot" in error for error in errors))

    def test_unknown_composition_is_rejected(self):
        segment = self.project["presentation_by_narrative"]["arc01.prologue.0001"][0]
        segment["direction"]["composition_id"] = "comp.arc01.prologue.unknown"
        self.assertTrue(any("invalid presentation composition" in error for error in self.errors()))

    def test_blackout_keeps_the_hero_slot_resolved(self):
        state = resolve_presentation_direction(
            self.project, "arc01.prologue.0006", "arc01.prologue.0006.p004"
        )
        visual = resolve_scene_visual_slots(self.project, state)
        self.assertEqual(visual["foreground"]["asset_type"], "hero_cg")
        self.assertEqual(visual["foreground"]["id"], "cg.arc01.prologue.final_moment")
        self.assertEqual(state["lighting"], "#000000ff")

    def test_art_plan_is_complete_and_spoiler_aware(self):
        plan = self.project["art_plans"][0]
        self.assertEqual(plan["scenes"], ["arc01.prologue.sc001"])
        self.assertEqual(plan["location"]["player_facing"], {"pt_BR": "—", "en": "—"})
        self.assertEqual(plan["production_inventory"]["backgrounds"], 1)
        self.assertEqual(plan["production_inventory"]["hero_cg_candidates"], 1)
        protagonist = self.project["art_character_by_id"]["character.natsuki_subaru"]
        self.assertEqual(protagonist["disclosure_threshold"], "arc01.prologue.0006.p004")
        self.assertEqual(self.errors(), [])

    def test_art_plan_validation_rejects_broken_references(self):
        requirement = self.project["art_plans"][0]["requirements"][0]
        requirement["scenes"] = ["missing.scene"]
        requirement["presentation_segments"] = ["missing.presentation"]
        requirement["category"] = "Poster"
        requirement["reuse_class"] = "Z"
        requirement["static"] = ""
        requirement["cinematic"] = ""
        requirement["reuse_of"] = "missing.asset"
        requirement["hero_candidate"] = True
        requirement["generation_spec"] = {}
        errors = self.errors()
        self.assertTrue(any("invalid art requirement scene" in error for error in errors))
        self.assertTrue(any("invalid art presentation reference" in error for error in errors))
        self.assertTrue(any("invalid art requirement category" in error for error in errors))
        self.assertTrue(any("invalid art reuse class" in error for error in errors))
        self.assertTrue(any("missing Static art plan" in error for error in errors))
        self.assertTrue(any("missing Cinematic art plan" in error for error in errors))
        self.assertTrue(any("invalid art reuse reference" in error for error in errors))
        self.assertTrue(any("invalid Hero CG reference" in error for error in errors))
        self.assertTrue(any("incomplete generation spec" in error for error in errors))

    def test_presentation_composition_must_cover_the_segment(self):
        segment = self.project["presentation_by_narrative"]["arc01.prologue.0001"][0]
        segment["direction"]["composition_id"] = "comp.arc01.prologue.black_boot"
        self.assertTrue(any("presentation composition lacks coverage" in error for error in self.errors()))

    def test_prologue_memory_unlocks_only_after_ending(self):
        memory = self.project["memory_by_id"]["memory.scene.arc01_prologue"]
        self.assertFalse(memory_unlocks(memory["unlock"], set(), set(), set()))
        self.assertFalse(memory_unlocks(memory["unlock"], {"arc01.prologue.0005"}, set(), {"arc01.prologue"}))
        self.assertTrue(memory_unlocks(memory["unlock"], {"arc01.prologue.0006"}, set(), {"arc01.prologue"}))

    def test_chapter_titles_are_independent_editions(self):
        chapter_id = "test.arc01.ch02"
        self.assertEqual(self.project["chapter_editions"]["pt_BR"][chapter_id]["title"], "Depois da Janela")
        self.assertEqual(self.project["chapter_editions"]["en"][chapter_id]["title"], "Beyond the Window")

    def test_missing_localized_chapter_is_rejected(self):
        chapter_id = self.project["chapter_order"][1]
        self.project["chapter_editions"]["en"].pop(chapter_id)
        self.assertIn("missing en chapter: " + chapter_id, self.errors())

    def test_narrative_cannot_belong_to_multiple_chapters(self):
        self.project["chapters"][1]["narrative_ids"].append("test.ch01.observatory.0001")
        self.assertIn("narrative belongs to multiple chapters: test.ch01.observatory.0001", self.errors())

    def test_locked_chapter_screen_does_not_embed_future_metadata(self):
        screen = (ROOT / "game/ui/chapters/chapters.rpy").read_text(encoding="utf-8")
        self.assertIn('text ui_text("locked_chapter")', screen)
        self.assertNotIn("metadata['title']", screen.split("else:", 1)[1])

    def test_progress_uses_explicit_canonical_order(self):
        index = {"later_in_data": 0, "earlier_in_data": 1}
        seen_ids, furthest_id = advance_progress(set(), None, "earlier_in_data", index)
        seen_ids, furthest_id = advance_progress(seen_ids, furthest_id, "later_in_data", index)
        self.assertEqual(seen_ids, {"later_in_data", "earlier_in_data"})
        self.assertEqual(furthest_id, "earlier_in_data")

    def test_revisiting_an_earlier_position_preserves_maximum_progress(self):
        index = self.project["narrative_index"]
        later_id = self.project["narrative_order"][4]
        earlier_id = self.project["narrative_order"][1]
        seen_ids, furthest_id = advance_progress(set(), None, later_id, index)
        seen_ids, furthest_id = advance_progress(seen_ids, furthest_id, earlier_id, index)
        self.assertEqual(furthest_id, later_id)
        self.assertEqual(seen_ids, {later_id, earlier_id})

    def test_stable_furthest_id_survives_narrative_reordering(self):
        original_index = {"first": 0, "furthest": 1, "later": 2}
        seen_ids, furthest_id = advance_progress(set(), None, "furthest", original_index)
        reordered_index = {"furthest": 0, "first": 1, "later": 2}
        self.assertEqual(canonical_furthest_id(furthest_id, seen_ids, reordered_index), "furthest")
        self.assertEqual(canonical_furthest_id("removed", {"first"}, reordered_index), "first")

    def test_memory_unlocks_and_future_entries_stay_hidden(self):
        early, future = self.project["memories"][0], self.project["memories"][1]
        seen = {"test.ch01.observatory.0001"}
        self.assertTrue(memory_unlocks(early["unlock"], seen, set(), set()))
        self.assertFalse(memory_unlocks(future["unlock"], seen, set(), set()))

    def test_memory_character_and_fact_unlocks_are_independent(self):
        character = self.project["memory_by_id"]["memory.character.lia"]
        seen = {"test.ch01.observatory.0002"}
        self.assertTrue(memory_unlocks(character["unlock"], seen, set(), set()))
        self.assertTrue(memory_unlocks(character["facts"][0]["unlock"], seen, set(), set()))
        self.assertFalse(memory_unlocks(character["facts"][1]["unlock"], seen, set(), set()))

    def test_memory_validation_rejects_bad_references_and_duplicate_ids(self):
        broken = copy.deepcopy(self.project["memories"][0])
        broken["id"] = self.project["memories"][0]["id"]
        broken["unlock"] = {"seen_id": "unknown"}
        self.project["memories"].append(broken)
        errors = self.errors()
        self.assertTrue(any("duplicate/empty memory ID" in error for error in errors))
        self.assertIn("invalid seen_id unlock: memory: " + broken["id"], errors)

    def test_fact_validation_rejects_invalid_conditions_and_duplicate_ids(self):
        character = self.project["memory_by_id"]["memory.character.lia"]
        fact = character["facts"][0]
        fact["unlock"] = {"seen_id": "missing"}
        self.assertIn("invalid seen_id unlock: fact: " + fact["id"], self.errors())
        fact["unlock"] = {"seen_scene": "missing"}
        self.assertIn("invalid seen_scene unlock: fact: " + fact["id"], self.errors())
        fact["unlock"] = {"chapter": "missing"}
        self.assertIn("invalid chapter unlock: fact: " + fact["id"], self.errors())
        fact["unlock"] = {"flag": "unsupported"}
        self.assertIn("invalid unlock condition: fact: " + fact["id"], self.errors())
        fact["unlock"] = {"seen_id": "test.ch01.observatory.0002"}
        character["facts"].append(copy.deepcopy(fact))
        self.assertIn("invalid memory fact: " + character["id"], self.errors())

    def test_memory_localization_requires_ui_fields(self):
        self.project["memory_editions"]["en"]["memory.illustration.observatory"].pop("title")
        self.assertIn("incomplete en memory metadata: memory.illustration.observatory", self.errors())
        self.project["memory_editions"]["pt_BR"]["memory.fact.lia.signal"]["text"] = ""
        self.assertIn("incomplete pt_BR memory fact: memory.fact.lia.signal", self.errors())

    def test_memory_localization_has_independent_editions(self):
        memory_id = "memory.illustration.observatory"
        self.assertEqual(self.project["memory_editions"]["pt_BR"][memory_id]["title"], "Luz no observatório")
        self.assertEqual(self.project["memory_editions"]["en"][memory_id]["title"], "Light at the Observatory")

    def test_manifest_combines_multiple_fragments_deterministically(self):
        with self.fragment_project() as root:
            project = load_project(root)
        self.assertEqual([entry["id"] for entry in project["narrative"]], ["fixture.0001", "fixture.0002"])
        self.assertEqual([entry["id"] for entry in project["scenes"]], ["fixture_scene_1", "fixture_scene_2"])
        self.assertEqual(project["editions"]["pt_BR"][1]["text"], "PT fragment two")
        self.assertEqual(project["narrative_index"], {"fixture.0001": 0, "fixture.0002": 1})

    def test_manifest_detects_duplicate_ids_between_fragments(self):
        with self.fragment_project(duplicate_narrative=True) as root:
            project = load_project(root)
            errors = validate(project, root)
        self.assertTrue(any("duplicate/empty narrative ID: fixture.0001" == error for error in errors))

    def test_manifest_detects_translation_missing_from_a_fragment(self):
        with self.fragment_project(missing_en_second=True) as root:
            project = load_project(root)
            errors = validate(project, root)
        self.assertIn("missing en: fixture.0002", errors)

    def fragment_project(self, duplicate_narrative=False, missing_en_second=False):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)

        def write(relative_path, content):
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(content), encoding="utf-8")

        narrative_ids = ["fixture.0001", "fixture.0001" if duplicate_narrative else "fixture.0002"]
        write("narrative/one.json", [{"id": narrative_ids[0], "scene": "fixture_scene_1"}])
        write("narrative/two.json", [{"id": narrative_ids[1], "scene": "fixture_scene_2"}])
        defaults = {"background": None, "music": None, "ambience": None, "lighting": "#00000000", "animation": "none"}
        write("scenes/one.json", [{"id": "fixture_scene_1", "defaults": defaults, "sequence": [{"dialogue": narrative_ids[0]}]}])
        write("scenes/two.json", [{"id": "fixture_scene_2", "defaults": defaults, "sequence": [{"dialogue": narrative_ids[1]}]}])
        for language, first_text, second_text in (("pt_BR", "PT fragment one", "PT fragment two"), ("en", "EN fragment one", "EN fragment two")):
            write(f"translations/{language}/one.json", [{"id": "fixture.0001", "speaker": "", "text": first_text}])
            write(f"translations/{language}/two.json", [{"id": "fixture.0002", "speaker": "", "text": second_text}])
            write(f"translations/{language}/ui.json", {"label": language})
        write("scenes/beats.json", {})
        write("assets/manifest.json", {"background": {}, "music": {}, "ambience": {}})
        chapters = [
            {"id": "fixture.ch01", "arc_id": "fixture.arc", "order": 1, "first_narrative_id": "fixture.0001", "last_narrative_id": "fixture.0001", "narrative_ids": ["fixture.0001"], "scenes": ["fixture_scene_1"]},
            {"id": "fixture.ch02", "arc_id": "fixture.arc", "order": 2, "first_narrative_id": "fixture.0002", "last_narrative_id": "fixture.0002", "narrative_ids": ["fixture.0002"], "scenes": ["fixture_scene_2"]},
        ]
        write("chapters/chapters.json", chapters)
        for language in ("pt_BR", "en"):
            write(f"translations/{language}/chapters.json", {
                "fixture.ch01": {"arc": "Arc", "chapter": "Chapter 1", "title": "One", "location": "Here"},
                "fixture.ch02": {"arc": "Arc", "chapter": "Chapter 2", "title": "Two", "location": "There"},
            })
        manifest = {
            "version": 1,
            "fragments": {
                "narrative": ["narrative/one.json", "narrative/two.json"],
                "scenes": ["scenes/one.json", "scenes/two.json"],
                "translations": {
                    "pt_BR": ["translations/pt_BR/one.json", "translations/pt_BR/two.json"],
                    "en": ["translations/en/one.json"] if missing_en_second else ["translations/en/one.json", "translations/en/two.json"],
                },
            },
            "narrative_order": ["fixture.0001", "fixture.0002"],
            "chapters": "chapters/chapters.json",
            "chapter_order": ["fixture.ch01", "fixture.ch02"],
            "chapter_translations": {"pt_BR": "translations/pt_BR/chapters.json", "en": "translations/en/chapters.json"},
            "beats": "scenes/beats.json",
            "assets": "assets/manifest.json",
            "ui": {"pt_BR": "translations/pt_BR/ui.json", "en": "translations/en/ui.json"},
        }
        write("content/manifest.json", manifest)
        return temporary

if __name__ == "__main__":
    unittest.main()
