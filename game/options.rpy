init -100 python:
    config.screen_width = 1920
    config.check_conflicting_properties = True
    config.screen_height = 1080
    config.name = "The Last Light — Technical Slice"
    config.version = "0.1.0"
    config.save_directory = "receba666-foundation"
    config.window_title = config.name
    config.default_text_cps = 38
    config.default_fullscreen = False
    config.allow_skipping = False
    config.has_autosave = True
    config.autosave_slots = 3
    config.history_length = 100
    config.main_menu_music = None
    config.game_menu_action = ShowMenu("pause_menu")
    config.quit_action = Quit(confirm=False)
    config.rollback_enabled = False

define narrator = Character(None)
define reader = Character("", dynamic=False)
