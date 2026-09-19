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
        prepare_position(persistent.resume_state["narrative_id"], False, persistent.resume_state.get("presentation_id"))

    def prepare_chapter_navigation(chapter_id):
        prepare_position(project_data["chapter_by_id"][chapter_id]["first_narrative_id"], True)

    def should_autosave_after_frame(chapter_changed):
        return chapter_changed or project_data["narrative_index"][current_id] % AUTOSAVE_INTERVAL == 0

    def next_presentation_id():
        segments = presentation_for(project_data, current_id)
        ids = [segment["id"] for segment in segments]
        position = ids.index(current_presentation_id) + 1
        return ids[position] if position < len(ids) else None

    def controlled_menu_exit():
        if current_id and store.reading_context == "normal":
            request_autosave("menu_exit")

    def begin_memory_replay(memory_id):
        memory = project_data["memory_by_id"][memory_id]
        store.memory_replay_snapshot = {
            "current_scene": current_scene, "current_id": current_id,
            "current_chapter": current_chapter, "frame_index": frame_index,
            "frames": frames, "director_state": dict(director_state),
            "chapter_opening_pending": chapter_opening_pending, "scene_change_pending": scene_change_pending,
        }
        store.memory_replay_target = memory
        store.reading_context = "memory_replay"
        prepare_position(memory["replay_start_id"], False)

    def restore_memory_replay():
        snapshot = store.memory_replay_snapshot
        store.reading_context = "normal"
        if snapshot:
            store.current_scene = snapshot["current_scene"]
            store.current_id = snapshot["current_id"]
            store.current_chapter = snapshot["current_chapter"]
            store.frame_index = snapshot["frame_index"]
            store.frames = snapshot["frames"]
            store.director_state = snapshot["director_state"]
            store.chapter_opening_pending = snapshot["chapter_opening_pending"]
            store.scene_change_pending = snapshot["scene_change_pending"]
            apply_direction(director_state)
        store.memory_replay_snapshot = None
        store.memory_replay_target = None

    def finish_memory_replay():
        restore_memory_replay()

    def cancel_memory_replay():
        restore_memory_replay()

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

label memory_replay_start:
    if not memory_replay_target or not is_memory_unlocked(memory_replay_target):
        jump main_menu
    $ begin_memory_replay(memory_replay_target)
    jump reading_loop

label memory_replay_return:
    call screen memories
    return

label memory_replay_cancel:
    $ cancel_memory_replay()
    hide screen scene_art onlayer master
    jump memory_replay_return

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
        if reading_context == "normal" and (chapter_changed or scene_change_pending or should_autosave_after_frame(False)):
            $ request_autosave("chapter_entry" if chapter_changed else ("scene_change" if scene_change_pending else "reading_interval"))
            $ scene_change_pending = False
        $ reader(presentation_text())
        $ next_presentation = next_presentation_id()
        if next_presentation is not None:
            $ store.current_presentation_id = next_presentation
            $ update_resume_position()
        else:
            if reading_context == "normal":
                $ record_position()
            if reading_context == "memory_replay" and current_id == memory_replay_target["replay_end_id"]:
                $ finish_memory_replay()
                hide screen scene_art onlayer master
                jump memory_replay_return
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
