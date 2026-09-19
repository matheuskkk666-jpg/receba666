# Native integration tests for journey, progression, and presentation.
init python:
    _test.screenshot_directory = "tests/artifacts"

testsuite foundation:
    setup:
        $ preferences.fullscreen = True
        $ persistent.edition = "pt_BR"
        $ persistent.presentation = "static"
        $ persistent.seen_ids = set()
        $ persistent.seen_scenes = set()
        $ persistent.furthest_position = -1
        $ persistent.furthest_narrative_id = None
        $ persistent.unlocked_chapter_ids = set()
        $ persistent.resume_state = None
        $ persistent.last_autosave_reason = None
        $ preferences.text_cps = 12
        $ os.environ["LN_PREVIEW_ID"] = "test.ch01.observatory.0001"
        run Function(renpy.restart_interaction)
        pause 0.2
    teardown:
        exit

    testcase journey_progression_continue_and_saves:
        assert screen "main_menu"
        assert eval not has_resume_state()
        assert eval renpy.get_widget("main_menu", "continue_journey") is None
        assert eval renpy.get_widget("main_menu", "journey_chapters") is None
        assert eval not config.rollback_enabled
        # Font rasterization can vary slightly between identical SDK runs; this is
        # below 0.1% of a 1920x1080 frame and does not mask layout changes.
        screenshot "m2-main-clean.png" max_pixel_difference 1500
        click id "start_journey"
        assert screen "chapter_card"
        pause 0.5
        screenshot "m2-chapter-card-pt.png" max_pixel_difference 1000
        pause 2.7
        assert screen "say"
        # One glyph may differ while the deterministic typewriter is active.
        screenshot "m2-reading-indicator-pt.png" max_pixel_difference 1200
        assert eval current_chapter == "test.arc01.ch01"
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval is_chapter_unlocked("test.arc01.ch01")
        assert eval not is_chapter_unlocked("test.arc01.ch02")
        assert eval persistent.resume_state["narrative_id"] == current_id
        assert eval persistent.furthest_narrative_id == current_id
        assert eval persistent.last_autosave_reason == "chapter_entry"
        advance
        assert eval current_id == "test.ch01.observatory.0002"
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("chapters")
        # The canonical prologue is now intentionally visible before technical fixtures.
        screenshot "m2-chapters-locked-pt.png" max_pixel_difference 1000
        click expression ui_text("back")
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("save")
        run FileSave(1, confirm=False)
        pause 0.3
        assert eval renpy.slot_json("1-1")["chapter_id"] == "test.arc01.ch01"
        assert eval "chapter_title" not in renpy.slot_json("1-1")
        assert eval slot_metadata(renpy.slot_json("1-1")["chapter_id"])["title"] == "A Última Luz"
        run Function(set_edition, "en")
        assert eval slot_metadata(renpy.slot_json("1-1")["chapter_id"])["title"] == "The Last Light"
        # Timestamped slots are asserted structurally; pixel baselines are not deterministic.
        run Function(set_edition, "pt_BR")
        assert eval slot_metadata(renpy.slot_json("1-1")["chapter_id"])["title"] == "A Última Luz"
        click expression ui_text("back")
        advance until screen "chapter_card"
        assert eval current_chapter == "test.arc01.ch02"
        pause 3.2
        assert screen "say"
        assert eval current_id == "test.ch02.rooftop.0001"
        assert eval is_chapter_unlocked("test.arc01.ch02")
        assert eval persistent.furthest_position == project_data["narrative_index"][current_id]
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("chapters")
        assert screen "chapters"
        assert eval is_chapter_unlocked("test.arc01.ch01") and is_chapter_unlocked("test.arc01.ch02")
        click expression chapter_button_label("test.arc01.ch01")
        assert screen "chapter_card"
        pause 3.2
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch02.rooftop.0001"]
        assert eval "test.ch02.rooftop.0001" in persistent.seen_ids
        run FileLoad(1, confirm=False)
        pause 0.5
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0002"
        assert eval current_chapter == "test.arc01.ch01"
        assert eval persistent.resume_state["narrative_id"] == "test.ch01.observatory.0002"
        assert eval not renpy.get_screen("chapter_card")
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch02.rooftop.0001"]
        assert eval is_chapter_unlocked("test.arc01.ch02")
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("main")
        click expression ui_text("yes")
        assert screen "main_menu"
        assert eval has_resume_state()
        assert eval renpy.get_widget("main_menu", "continue_journey") is not None
        assert eval renpy.get_widget("main_menu", "journey_chapters") is not None
        click id "continue_journey"
        pause 0.3
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0002"
        assert eval current_chapter == "test.arc01.ch01"
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("main")
        click expression ui_text("yes")
        click id "start_journey"
        assert screen "confirm"
        click expression ui_text("yes")
        assert screen "chapter_card"
        pause 3.2
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch02.rooftop.0001"]
        assert eval is_chapter_unlocked("test.arc01.ch02")
        run MainMenu(confirm=False)
        assert screen "main_menu"

    testcase presentation_and_language_matrix:
        parameter language = ["pt_BR", "en"]
        parameter mode = ["static", "cinematic"]
        run Function(set_edition, language)
        run Function(set_presentation, mode)
        assert eval has_resume_state()
        click id "continue_journey" until screen "say"
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval persistent.edition == language
        assert eval persistent.presentation == mode
        assert eval director_state == resolve(project_data, "test_observatory")[0]["state"]
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("settings")
        click expression ("English" if language == "pt_BR" else "Português (Brasil)")
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval current_chapter == "test.arc01.ch01"
        assert eval director_state == resolve(project_data, "test_observatory")[0]["state"]
        assert eval persistent.presentation == mode
        click expression ui_text("back")
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("main")
        click expression ui_text("yes")
        assert screen "main_menu"

    testcase completion_clears_resume_and_keeps_chapters:
        assert screen "main_menu"
        assert eval has_resume_state()
        $ persistent.edition = "pt_BR"
        $ _history_list[:] = []
        click id "continue_journey" until screen "say"
        advance until screen "main_menu"
        assert eval current_id == "test.ch02.rooftop.0003"
        assert eval not has_resume_state()
        assert eval renpy.get_widget("main_menu", "continue_journey") is None
        assert eval renpy.get_widget("main_menu", "journey_chapters") is not None
        assert eval is_chapter_unlocked("test.arc01.ch01") and is_chapter_unlocked("test.arc01.ch02")
        assert eval sum(1 for entry in _history_list if getattr(entry, "narrative_id", None) == "test.ch02.rooftop.0003") == 1
        click id "journey_chapters"
        assert screen "chapters"
        click expression chapter_button_label("test.arc01.ch01")
        assert screen "chapter_card"
        pause 3.2
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0001"
        run MainMenu(confirm=False)
        assert screen "main_menu"

    testcase legacy_m1_progress_migrates_without_resume:
        assert screen "main_menu"
        $ persistent.seen_ids = set()
        $ persistent.furthest_position = -1
        $ persistent.furthest_narrative_id = None
        $ persistent.unlocked_chapter_ids = set()
        $ persistent.resume_state = {"chapter_id": "bad", "scene_id": "bad", "narrative_id": "bad"}
        $ persistent.furthest_ids = {"test.ch01.observatory.0006"}
        run Function(migrate_legacy_progress)
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch01.observatory.0006"]
        assert eval persistent.furthest_narrative_id == "test.ch01.observatory.0006"
        assert eval is_chapter_unlocked("test.arc01.ch01")
        assert eval not is_chapter_unlocked("test.arc01.ch02")
        assert eval not has_resume_state()

    testcase generic_confirmation_uses_its_own_message:
        assert screen "main_menu"
        run Confirm("GENERIC CONFIRMATION MESSAGE", NullAction(), NullAction())
        assert screen "confirm"
        assert id "confirm_message"
        click expression ui_text("no") until not screen "confirm"
        assert screen "main_menu"

    testcase memories_unlocks_and_replay_are_isolated:
        $ persistent.edition = "pt_BR"
        $ persistent.seen_ids = set()
        $ persistent.seen_scenes = set()
        $ persistent.furthest_narrative_id = None
        $ persistent.furthest_position = -1
        $ persistent.unlocked_chapter_ids = set()
        $ persistent.resume_state = None
        click id "start_journey" until screen "say"
        assert eval is_memory_unlocked("memory.illustration.observatory")
        assert eval not is_memory_unlocked("memory.illustration.window")
        assert eval not is_memory_unlocked("memory.death.fading_signal")
        advance
        assert eval current_id == "test.ch01.observatory.0002"
        run MainMenu(confirm=False)
        assert screen "main_menu"
        assert eval renpy.get_widget("main_menu", "journey_memories") is not None
        click id "journey_memories"
        assert screen "memories"
        click expression ui_text("illustrations")
        assert screen "memory_category"
        assert eval len(memory_entries("illustrations")) == 1
        click expression memory_metadata("memory.illustration.observatory")["title"]
        assert screen "memory_illustration"
        click expression ui_text("back")
        click expression ui_text("back")
        click expression ui_text("characters")
        assert eval len(memory_entries("characters")) == 1
        click expression memory_metadata("memory.character.lia")["name"]
        assert screen "memory_character"
        assert eval len(unlocked_memory_facts("memory.character.lia")) == 1
        click expression ui_text("back")
        click expression ui_text("back")
        click expression ui_text("scenes")
        $ replay_resume = dict(persistent.resume_state)
        $ replay_seen = set(persistent.seen_ids)
        $ replay_furthest = persistent.furthest_narrative_id
        click expression memory_metadata("memory.scene.first_signal")["title"] until screen "say"
        assert eval reading_context == "memory_replay"
        advance until screen "memories"
        assert eval reading_context == "normal"
        assert eval persistent.resume_state == replay_resume
        assert eval persistent.seen_ids == replay_seen
        assert eval persistent.furthest_narrative_id == replay_furthest
        $ cancel_resume = dict(persistent.resume_state)
        $ cancel_seen = set(persistent.seen_ids)
        $ cancel_scenes = set(persistent.seen_scenes)
        $ cancel_furthest = persistent.furthest_narrative_id
        $ cancel_chapters = set(persistent.unlocked_chapter_ids)
        click expression ui_text("scenes")
        click expression memory_metadata("memory.scene.first_signal")["title"] until screen "say"
        run ShowMenu("pause_menu")
        assert screen "pause_menu"
        assert eval renpy.get_widget("pause_menu", "pause_save") is None
        assert eval renpy.get_widget("pause_menu", "pause_load") is None
        assert eval renpy.get_widget("pause_menu", "pause_chapters") is None
        assert eval renpy.get_widget("pause_menu", "pause_main") is None
        click id "return_memories"
        assert screen "memories"
        assert eval reading_context == "normal"
        assert eval memory_replay_target is None and memory_replay_snapshot is None
        assert eval persistent.resume_state == cancel_resume
        assert eval persistent.seen_ids == cancel_seen
        assert eval persistent.seen_scenes == cancel_scenes
        assert eval persistent.furthest_narrative_id == cancel_furthest
        assert eval persistent.unlocked_chapter_ids == cancel_chapters
        click expression ui_text("back") until screen "main_menu"
        click id "continue_journey" until screen "say"
        assert eval current_id == "test.ch01.observatory.0002"

    testcase real_prologue_starts_and_advances_by_segment:
        $ os.environ.pop("LN_PREVIEW_ID", None)
        $ persistent.resume_state = None
        run MainMenu(confirm=False)
        click id "start_journey" until screen "say"
        assert eval current_id == "arc01.prologue.0001"
        assert eval current_presentation_id == "arc01.prologue.0001.p001"
        assert eval current_scene == "arc01.prologue.sc001"
        assert eval director_state["background"] == "prologue_ground_placeholder"
        assert eval "observatory" not in str(director_state)
        advance
        assert eval current_id == "arc01.prologue.0001"
        assert eval current_presentation_id == "arc01.prologue.0001.p002"
        advance until eval current_id == "arc01.prologue.0003" and current_presentation_id == "arc01.prologue.0003.p003"
        assert eval director_state["composition_id"] == "comp.arc01.prologue.black_boot"
        assert eval director_state["lighting"] == "#09070fbd"
        advance until eval current_id == "arc01.prologue.0004" and current_presentation_id == "arc01.prologue.0004.p003"
        assert eval presentation_segment(project_data, current_id, current_presentation_id)["kind"] == "dialogue"
        pause 1.0
        screenshot "m5-prologue-dialogue-pt.png" max_pixel_difference 500
        run Function(set_edition, "en")
        assert eval current_id == "arc01.prologue.0004"
        assert eval current_presentation_id == "arc01.prologue.0004.p003"
        pause 1.0
        screenshot "m5-prologue-dialogue-en.png" max_pixel_difference 500
        run Function(set_edition, "pt_BR")
        assert eval current_presentation_id == "arc01.prologue.0004.p003"
        run Function(set_presentation, "cinematic")
        assert eval director_state["composition_id"] == "comp.arc01.prologue.second_arrival"
        run FileSave(2, confirm=False)
        run FileLoad(2, confirm=False)
        assert eval current_presentation_id == "arc01.prologue.0004.p003"
        run MainMenu(confirm=False)
        click id "continue_journey" until screen "say"
        assert eval current_presentation_id == "arc01.prologue.0004.p003"
        advance until eval current_id == "arc01.prologue.0006" and current_presentation_id == "arc01.prologue.0006.p004"
        assert eval director_state["composition_id"] == "cg.arc01.prologue.final_moment"
        assert eval director_state["lighting"] == "#000000ff"
        assert eval director_state["animation"] == "none"
        advance until screen "main_menu"
        assert eval "arc01.prologue.0006" in persistent.seen_ids
        assert eval not has_resume_state()
        assert eval is_memory_unlocked("memory.scene.arc01_prologue")
        $ prologue_seen = set(persistent.seen_ids)
        $ prologue_furthest = persistent.furthest_narrative_id
        $ prologue_chapters = set(persistent.unlocked_chapter_ids)
        click id "journey_memories"
        click expression ui_text("scenes")
        click expression memory_metadata("memory.scene.arc01_prologue")["title"] until screen "say"
        assert eval reading_context == "memory_replay"
        assert eval current_presentation_id == "arc01.prologue.0001.p001"
        advance until screen "memories"
        assert eval reading_context == "normal"
        assert eval memory_replay_target is None and memory_replay_snapshot is None
        assert eval persistent.seen_ids == prologue_seen
        assert eval persistent.furthest_narrative_id == prologue_furthest
        assert eval persistent.unlocked_chapter_ids == prologue_chapters
        assert eval not has_resume_state()
