# Only narrative and resolved direction belong to save slots; edition/mode are preferences.
default current_scene = None
default current_id = None
default frame_index = 0
default frames = []
default director_state = {}
default persistent.seen_scenes = set()
default persistent.furthest_ids = set()

init python:
    def record_position():
        persistent.seen_scenes.add(current_scene)
        persistent.furthest_ids.add(current_id)
    def save_metadata(data):
        data["narrative_id"] = current_id
        data["scene"] = current_scene
        data["schema"] = 1
    config.save_json_callbacks.append(save_metadata)

label after_load:
    $ apply_direction(director_state)
    return
