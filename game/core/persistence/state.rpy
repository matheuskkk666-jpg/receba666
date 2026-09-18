# Only narrative and resolved direction belong to save slots; edition/mode are preferences.
default current_scene = None
default current_id = None
default current_chapter = None
default chapter_opening_pending = False
default chapter_navigation_target = None
default scene_change_pending = False
default frame_index = 0
default frames = []
default director_state = {}
default persistent.seen_scenes = set()
default persistent.seen_ids = set()
default persistent.furthest_position = -1
default persistent.unlocked_chapter_ids = set()
default persistent.resume_state = None
default persistent.progress_schema = 2
default persistent.last_autosave_reason = None

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
        persistent.unlocked_chapter_ids = {
            chapter_id
            for chapter_id in (getattr(persistent, "unlocked_chapter_ids", set()) or ())
            if chapter_id in project_data["chapter_by_id"]
        }
        persistent.unlocked_chapter_ids.update(
            unlocked_chapters(project_data, persistent.furthest_position)
        )
        resume_state = getattr(persistent, "resume_state", None)
        if not is_valid_resume_state(resume_state):
            persistent.resume_state = None
        else:
            persistent.resume_state = dict(resume_state)
        persistent.progress_schema = 2

    def is_valid_resume_state(state):
        if not isinstance(state, dict):
            return False
        narrative_id = state.get("narrative_id")
        chapter_id = state.get("chapter_id")
        scene_id = state.get("scene_id")
        if narrative_id not in project_data["narrative_by_id"]:
            return False
        return (
            chapter_id == chapter_for_narrative(project_data, narrative_id)
            and scene_id == project_data["narrative_by_id"][narrative_id]["scene"]
        )

    def has_resume_state():
        return is_valid_resume_state(getattr(persistent, "resume_state", None))

    def is_chapter_unlocked(chapter_id):
        return chapter_id in persistent.unlocked_chapter_ids

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
        store.current_chapter = chapter_for_narrative(project_data, current_id)
        persistent.unlocked_chapter_ids.add(current_chapter)
        persistent.resume_state = {
            "schema": 2,
            "chapter_id": current_chapter,
            "scene_id": current_scene,
            "narrative_id": current_id,
        }

    def furthest_narrative_id():
        if persistent.furthest_position < 0:
            return None
        return project_data["narrative_order"][persistent.furthest_position]

    def save_metadata(data):
        data["narrative_id"] = current_id
        data["scene"] = current_scene
        data["chapter_id"] = current_chapter
        if current_chapter:
            metadata = chapter_metadata(current_chapter)
            data.update({
                "arc": metadata["arc"],
                "chapter": metadata["chapter"],
                "chapter_title": metadata["title"],
                "location": metadata["location"],
            })
        data["schema"] = 2
    config.save_json_callbacks.append(save_metadata)
    migrate_legacy_progress()

label after_load:
    $ apply_direction(director_state)
    return
