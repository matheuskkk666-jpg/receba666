init python:
    def enter_scene(scene_id):
        store.current_scene = scene_id
        store.frames = resolve(project_data, scene_id)
        store.frame_index = 0

    def enter_frame(index):
        frame = frames[index]
        store.current_id = frame["id"]
        store.director_state = dict(frame["state"])
        record_position()
        apply_direction(director_state)

    def apply_direction(state):
        apply_audio(state)

    def set_presentation(mode):
        persistent.presentation = mode
        renpy.save_persistent()
        renpy.restart_interaction()
