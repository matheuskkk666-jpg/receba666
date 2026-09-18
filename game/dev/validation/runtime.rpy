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
        $ persistent.unlocked_chapter_ids = set()
        $ persistent.resume_state = None
        $ persistent.last_autosave_reason = None
        $ preferences.text_cps = 12
        run Function(renpy.restart_interaction)
        pause 0.2
    teardown:
        exit

    testcase journey_progression_continue_and_saves:
        assert screen "main_menu"
        assert eval not has_resume_state()
        assert eval renpy.get_widget("main_menu", "continue_journey") is None
        assert eval not config.rollback_enabled
        screenshot "m2-main-clean.png"
        click id "start_journey"
        assert screen "chapter_card"
        pause 0.5
        screenshot "m2-chapter-card-pt.png"
        pause 2.7
        assert screen "say"
        screenshot "m2-reading-indicator-pt.png"
        assert eval current_chapter == "test.arc01.ch01"
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval is_chapter_unlocked("test.arc01.ch01")
        assert eval not is_chapter_unlocked("test.arc01.ch02")
        assert eval persistent.resume_state["narrative_id"] == current_id
        assert eval persistent.last_autosave_reason == "chapter_entry"
        advance
        assert eval current_id == "test.ch01.observatory.0002"
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("chapters")
        screenshot "m2-chapters-locked-pt.png"
        click expression ui_text("back")
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        click expression ui_text("save")
        run FileSave(1, confirm=False)
        pause 0.3
        assert eval renpy.slot_json("1-1")["chapter_id"] == "test.arc01.ch01"
        assert eval renpy.slot_json("1-1")["chapter_title"] == "A Última Luz"
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

    testcase legacy_m1_progress_migrates_without_resume:
        assert screen "main_menu"
        $ persistent.seen_ids = set()
        $ persistent.furthest_position = -1
        $ persistent.unlocked_chapter_ids = set()
        $ persistent.resume_state = {"chapter_id": "bad", "scene_id": "bad", "narrative_id": "bad"}
        $ persistent.furthest_ids = {"test.ch01.observatory.0006"}
        run Function(migrate_legacy_progress)
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch01.observatory.0006"]
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
