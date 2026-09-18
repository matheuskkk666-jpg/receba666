init python:
    def enter_scene(scene_id):
        store.current_scene = scene_id
        store.frames = resolve(project_data, scene_id)
        store.frame_index = 0

    def prepare_position(narrative_id, show_chapter_opening=False):
        scene_id = project_data["narrative_by_id"][narrative_id]["scene"]
        previous_scene = store.current_scene
        enter_scene(scene_id)
        store.frame_index = next(index for index, frame in enumerate(frames) if frame["id"] == narrative_id)
        store.current_id = None
        store.current_chapter = None if show_chapter_opening else chapter_for_narrative(project_data, narrative_id)
        store.chapter_opening_pending = show_chapter_opening
        store.scene_change_pending = previous_scene is not None and previous_scene != scene_id
        store.director_state = dict(frames[frame_index]["state"])
        apply_direction(director_state)

    def enter_frame(index):
        frame = frames[index]
        store.current_id = frame["id"]
        store.director_state = dict(frame["state"])
        record_position()
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
