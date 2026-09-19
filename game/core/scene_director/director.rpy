init python:
    def enter_scene(scene_id):
        if store.current_scene == scene_id and store.frames:
            return False
        store.current_scene = scene_id
        store.frames = project_data["frames_by_scene"][scene_id]
        store.frame_index = 0
        return True

    def prepare_position(narrative_id, show_chapter_opening=False, presentation_id=None):
        scene_id = project_data["narrative_to_scene"][narrative_id]
        previous_scene = store.current_scene
        scene_changed = enter_scene(scene_id)
        store.frame_index = project_data["frame_index_by_narrative"][narrative_id]
        store.current_id = None
        available_segments = presentation_for(project_data, narrative_id)
        valid_ids = {segment["id"] for segment in available_segments}
        store.current_presentation_id = presentation_id if presentation_id in valid_ids else available_segments[0]["id"]
        store.current_chapter = None if show_chapter_opening else chapter_for_narrative(project_data, narrative_id)
        store.chapter_opening_pending = show_chapter_opening
        store.scene_change_pending = previous_scene is not None and scene_changed
        store.director_state = dict(frames[frame_index]["state"])
        apply_direction(director_state)

    def enter_frame(index):
        frame = frames[index]
        store.current_id = frame["id"]
        store.director_state = dict(frame["state"])
        if presentation_for(project_data, current_id)[0].get("synthetic"):
            record_position()
        else:
            update_resume_position()
        apply_direction(director_state)

    def next_narrative_id():
        position = project_data["narrative_index"][current_id] + 1
        if position >= len(project_data["narrative_order"]):
            return None
        return project_data["narrative_order"][position]

    def apply_direction(state):
        apply_audio(state)

    def set_presentation(mode):
        persistent.presentation = mode
        renpy.save_persistent()
        renpy.restart_interaction()
