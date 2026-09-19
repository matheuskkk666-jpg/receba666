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
default persistent.furthest_narrative_id = None
default persistent.unlocked_chapter_ids = set()
default persistent.resume_state = None
default persistent.progress_schema = 2
default persistent.last_autosave_reason = None
default reading_context = "normal"
default memory_replay_target = None
default memory_replay_snapshot = None

init python:
    def migrate_legacy_progress():
        persistent.seen_ids = {
            narrative_id
            for narrative_id in (getattr(persistent, "seen_ids", set()) or ())
            if narrative_id in project_data["narrative_index"]
        }
        legacy_position = getattr(persistent, "furthest_position", -1)
        if not isinstance(legacy_position, int):
            legacy_position = -1
        legacy_seen_ids = set(getattr(persistent, "furthest_ids", set()) or ())
        persistent.seen_ids.update(narrative_id for narrative_id in legacy_seen_ids if narrative_id in project_data["narrative_index"])
        legacy_furthest_id = getattr(persistent, "furthest_narrative_id", None)
        if legacy_furthest_id is None and getattr(persistent, "progress_schema", 0) < 3:
            legacy_furthest_id = (
                project_data["narrative_order"][legacy_position]
                if 0 <= legacy_position < len(project_data["narrative_order"])
                else None
            )
        persistent.furthest_narrative_id = canonical_furthest_id(
            legacy_furthest_id,
            persistent.seen_ids,
            project_data["narrative_index"],
        )
        persistent.furthest_position = (
            project_data["narrative_index"][persistent.furthest_narrative_id]
            if persistent.furthest_narrative_id else -1
        )
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
        persistent.progress_schema = 3

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

    def has_journey_progress():
        return bool(persistent.unlocked_chapter_ids)

    def unlock_condition_met(condition):
        return memory_unlocks(condition, persistent.seen_ids, persistent.seen_scenes, persistent.unlocked_chapter_ids)

    def is_memory_unlocked(memory_id):
        memory = project_data["memory_by_id"].get(memory_id)
        return bool(memory and unlock_condition_met(memory["unlock"]))

    def memory_entries(category):
        return [entry for entry in project_data["memories"] if entry["category"] == category and is_memory_unlocked(entry["id"])]

    def has_memories():
        return any(is_memory_unlocked(entry["id"]) for entry in project_data["memories"])

    def unlocked_memory_facts(memory_id):
        memory = project_data["memory_by_id"][memory_id]
        return [fact for fact in memory.get("facts", []) if unlock_condition_met(fact["unlock"])]

    def is_chapter_unlocked(chapter_id):
        return chapter_id in persistent.unlocked_chapter_ids

    def complete_journey():
        persistent.resume_state = None

    def synchronize_resume_after_load():
        if current_id not in project_data["narrative_by_id"]:
            persistent.resume_state = None
            return
        scene_id = project_data["narrative_to_scene"][current_id]
        if current_scene != scene_id:
            persistent.resume_state = None
            return
        chapter_id = chapter_for_narrative(project_data, current_id)
        store.current_chapter = chapter_id
        persistent.resume_state = {
            "schema": 3,
            "chapter_id": chapter_id,
            "scene_id": scene_id,
            "narrative_id": current_id,
        }
        renpy.save_persistent()

    def record_position():
        persistent.seen_scenes.add(current_scene)
        seen_ids, furthest_narrative_id = advance_progress(
            persistent.seen_ids,
            persistent.furthest_narrative_id,
            current_id,
            project_data["narrative_index"],
        )
        persistent.seen_ids = seen_ids
        persistent.furthest_narrative_id = furthest_narrative_id
        persistent.furthest_position = project_data["narrative_index"][furthest_narrative_id]
        store.current_chapter = chapter_for_narrative(project_data, current_id)
        persistent.unlocked_chapter_ids.add(current_chapter)
        persistent.resume_state = {
            "schema": 3,
            "chapter_id": current_chapter,
            "scene_id": current_scene,
            "narrative_id": current_id,
        }

    def furthest_narrative_id():
        return canonical_furthest_id(
            persistent.furthest_narrative_id,
            persistent.seen_ids,
            project_data["narrative_index"],
        )

    def save_metadata(data):
        data["narrative_id"] = current_id
        data["scene"] = current_scene
        data["chapter_id"] = current_chapter
        data["schema"] = 3
    config.save_json_callbacks.append(save_metadata)
    migrate_legacy_progress()

label after_load:
    $ synchronize_resume_after_load()
    $ apply_direction(director_state)
    return
