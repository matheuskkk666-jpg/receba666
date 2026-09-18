# Native engine integration tests. Executed only by the SDK's `test` command.
init python:
    _test.screenshot_directory = "tests/artifacts"

testsuite foundation:
    setup:
        $ preferences.fullscreen = True
        $ persistent.edition = "pt_BR"
        $ persistent.presentation = "static"
        $ persistent.seen_ids = set()
        $ persistent.furthest_position = -1
        $ preferences.text_cps = 12
        run Function(renpy.restart_interaction)
        pause 0.2
    teardown:
        exit

    testcase reading_flow:
        assert screen "main_menu"
        assert eval not config.rollback_enabled
        screenshot "01-main-pt.png"
        click "Começar Jornada"
        pause 0.4
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval renpy.get_widget("say", "what").slow
        click pos (1000, 700)
        pause 0.2
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval not renpy.get_widget("say", "what").slow
        screenshot "02-reading-pt.png"
        click pos (1000, 700)
        pause 0.2
        assert eval current_id == "test.ch01.observatory.0002"
        keysym "K_SPACE"
        pause 0.2
        assert eval current_id == "test.ch01.observatory.0002"
        screenshot "03-speaker-pt.png"
        click id "hide_ui"
        pause 0.2
        screenshot "04-hidden.png"
        assert screen "scene_art" layer "master"
        click pos (1000, 700)
        pause 0.2
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0002"
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        assert screen "scene_art" layer "master"
        screenshot "05-pause-pt.png"
        click "Configurações"
        assert screen "settings"
        screenshot "06-settings-pt.png"
        click "English"
        assert eval persistent.edition == "en"
        assert eval current_id == "test.ch01.observatory.0002"
        click "Cinematic"
        screenshot "07-settings-en.png"
        click "Back"
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0002"
        assert eval persistent.presentation == "cinematic"
        pause 0.3
        screenshot "08-reading-en.png"
        keysym "K_ESCAPE"
        click "Resume"
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0002"
        assert eval not renpy.get_widget("say", "what").slow
        advance
        assert eval current_id == "test.ch01.observatory.0003"
        advance
        assert eval current_id == "test.ch01.observatory.0004"
        assert eval director_state["lighting"] == "#09112738"
        assert eval persistent.furthest_position == project_data["narrative_index"][current_id]
        keysym "K_ESCAPE"
        click "Save"
        assert screen "save"
        screenshot "09-save-en.png"
        run FileSave(1, confirm=False)
        pause 0.5
        click "Back"
        advance
        assert eval current_id == "test.ch01.observatory.0005"
        assert eval director_state["lighting"] == "#00000000"
        keysym "K_ESCAPE"
        click "Settings"
        click "Português (Brasil)"
        click "Estático"
        click "Voltar"
        keysym "K_ESCAPE"
        click "Carregar"
        run FileLoad(1, confirm=False)
        pause 0.5
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0004"
        assert eval director_state["lighting"] == "#09112738"
        assert eval director_state == frames[3]["state"]
        assert eval persistent.edition == "pt_BR"
        assert eval persistent.presentation == "static"
        assert eval persistent.furthest_position == project_data["narrative_index"]["test.ch01.observatory.0005"]
        screenshot "10-restored-pt.png"
        keysym "K_ESCAPE"
        click "Histórico"
        assert eval all(history_entry(h)["text"] == edition_index["pt_BR"][h.narrative_id]["text"] for h in _history_list)
        screenshot "11-history-pt.png"
        click "Voltar"
        assert eval current_id == "test.ch01.observatory.0004"
        keysym "K_ESCAPE"
        click "Capítulos"
        screenshot "12-chapters-pt.png"
        click "Voltar"
        keysym "K_ESCAPE"
        click "Menu Principal"
        assert id "confirm_message"
        click "Confirmar"
        assert screen "main_menu"
        click "Configurações"
        click "English"
        click "Back"
        assert screen "main_menu"
        screenshot "13-main-en.png"
        click "Start Journey"
        assert eval current_id == "test.ch01.observatory.0001"
        advance until screen "main_menu"

    testcase generic_confirmation_uses_its_own_message:
        assert screen "main_menu"
        run Confirm("GENERIC CONFIRMATION MESSAGE", NullAction(), NullAction())
        assert screen "confirm"
        assert id "confirm_message"
        click expression ui_text("no") until not screen "confirm"
        assert screen "main_menu"

    testcase presentation_matrix:
        parameter language = ["pt_BR", "en"]
        parameter mode = ["static", "cinematic"]
        run Function(set_edition, language)
        run Function(set_presentation, mode)
        click expression ui_text("start") until screen "say"
        click pos (1000, 700)
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval director_state == resolve(project_data, "test_observatory")[0]["state"]
        screenshot f"matrix-{language}-{mode}-a.png"
        pause 2.0
        screenshot f"matrix-{language}-{mode}-b.png"
        keysym "K_ESCAPE"
        assert screen "pause_menu"
        screenshot f"pause-{language}-{mode}.png"
        keysym "K_ESCAPE"
        assert screen "say"
        assert eval current_id == "test.ch01.observatory.0001"
        assert eval not renpy.get_widget("say", "what").slow
        keysym "K_SPACE"
        assert eval current_id == "test.ch01.observatory.0002"
        keysym "K_ESCAPE"
        click expression ui_text("save")
        click pos (500, 400)
        pause 0.2
        screenshot f"slots-{language}-{mode}.png"
        click expression ui_text("back")
        advance
        assert eval current_id == "test.ch01.observatory.0003"
        keysym "K_ESCAPE"
        click expression ui_text("load")
        click pos (500, 400)
        assert eval current_id == "test.ch01.observatory.0002"
        assert eval director_state == frames[1]["state"]
        assert eval persistent.edition == language
        assert eval persistent.presentation == mode
        run MainMenu(confirm=False)
        assert screen "main_menu"
