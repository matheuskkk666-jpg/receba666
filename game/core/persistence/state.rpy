# Only narrative and resolved direction belong to save slots; edition/mode are preferences.
default current_scene = None
default current_id = None
default frame_index = 0
default frames = []
default director_state = {}
default persistent.seen_scenes = set()
default persistent.seen_ids = set()
default persistent.furthest_position = -1

init python:
    def migrate_legacy_progress():
        persistent.seen_ids = {
            narrative_id
            for narrative_id in (getattr(persistent, "seen_ids", set()) or ())
            if narrative_id in project_data["narrative_index"]
        }
        persistent.furthest_position = getattr(persistent, "furthest_position", -1)
        if not isinstance(persistent.furthest_position, int):
            persistent.furthest_position = -1
        persistent.furthest_position = min(
            persistent.furthest_position,
            len(project_data["narrative_order"]) - 1,
        )
        legacy_seen_ids = set(getattr(persistent, "furthest_ids", set()) or ())
        persistent.seen_ids.update(narrative_id for narrative_id in legacy_seen_ids if narrative_id in project_data["narrative_index"])
        legacy_position = max(
            (project_data["narrative_index"][narrative_id] for narrative_id in persistent.seen_ids),
            default=-1,
        )
        persistent.furthest_position = max(persistent.furthest_position, legacy_position)

    def record_position():
        persistent.seen_scenes.add(current_scene)
        seen_ids, furthest_position = advance_progress(
            persistent.seen_ids,
            persistent.furthest_position,
            current_id,
            project_data["narrative_index"],
        )
        persistent.seen_ids = seen_ids
        persistent.furthest_position = furthest_position

    def furthest_narrative_id():
        if persistent.furthest_position < 0:
            return None
        return project_data["narrative_order"][persistent.furthest_position]

    def save_metadata(data):
        data["narrative_id"] = current_id
        data["scene"] = current_scene
        data["schema"] = 1
    config.save_json_callbacks.append(save_metadata)
    migrate_legacy_progress()

label after_load:
    $ apply_direction(director_state)
    return
