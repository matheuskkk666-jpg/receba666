init python:
    import os
    AUTOSAVE_INTERVAL = 3

    def request_autosave(reason):
        persistent.last_autosave_reason = reason
        renpy.save_persistent()
        renpy.force_autosave(take_screenshot=True, block=False)

    def prepare_new_journey():
        preview_id = os.environ.get("LN_PREVIEW_ID")
        preview_scene_id = os.environ.get("LN_PREVIEW_SCENE")
        if preview_id in project_data["narrative_by_id"]:
            start_id = preview_id
        elif preview_scene_id:
            start_id = next(entry["id"] for entry in project_data["narrative"] if entry["scene"] == preview_scene_id)
        else:
            first_chapter = project_data["chapter_order"][0]
            start_id = project_data["chapter_by_id"][first_chapter]["first_narrative_id"]
        prepare_position(start_id, True)

    def prepare_continue():
        prepare_position(persistent.resume_state["narrative_id"], False)

    def prepare_chapter_navigation(chapter_id):
        prepare_position(project_data["chapter_by_id"][chapter_id]["first_narrative_id"], True)

    def should_autosave_after_frame(chapter_changed):
        return chapter_changed or project_data["narrative_index"][current_id] % AUTOSAVE_INTERVAL == 0

    def controlled_menu_exit():
        if current_id:
            request_autosave("menu_exit")

label start:
    jump journey_start

label journey_start:
    $ prepare_new_journey()
    jump reading_loop

label continue_journey:
    if not has_resume_state():
        jump main_menu
    $ prepare_continue()
    jump reading_loop

label chapter_start:
    if not chapter_navigation_target or not is_chapter_unlocked(chapter_navigation_target):
        jump main_menu
    $ prepare_chapter_navigation(chapter_navigation_target)
    jump reading_loop

label reading_loop:
    show screen scene_art onlayer master
    $ journey_finished = False
    while not journey_finished:
        $ pending_id = frames[frame_index]["id"]
        $ pending_chapter = chapter_for_narrative(project_data, pending_id)
        $ chapter_changed = current_chapter != pending_chapter
        if chapter_changed:
            $ current_chapter = pending_chapter
            if chapter_opening_pending:
                call chapter_opening
                $ chapter_opening_pending = False
            show screen journey_indicator(current_chapter)
        $ enter_frame(frame_index)
        if chapter_changed or scene_change_pending or should_autosave_after_frame(False):
            $ request_autosave("chapter_entry" if chapter_changed else ("scene_change" if scene_change_pending else "reading_interval"))
            $ scene_change_pending = False
        $ reader(localized_entry().get("text", ""))
        $ next_id = next_narrative_id()
        if next_id is not None:
            $ next_chapter = chapter_for_narrative(project_data, next_id)
            $ prepare_position(next_id, next_chapter != current_chapter)
        else:
            $ complete_journey()
            $ request_autosave("journey_complete")
            $ journey_finished = True
    hide screen scene_art onlayer master
    $ renpy.music.stop(channel="music", fadeout=1.0)
    $ renpy.music.stop(channel="ambience", fadeout=1.0)
    jump main_menu
