import copy
import json
from pathlib import Path

LANGUAGES = ("pt_BR", "en")

def load_project(root, read=None):
    root = Path(root)
    def get(path):
        if read:
            return json.loads(read(path))
        return json.loads((root / path).read_text(encoding="utf-8"))

    manifest = get("content/manifest.json")
    if manifest.get("version") != 1:
        raise ValueError("unsupported content manifest version")

    fragments = manifest["fragments"]

    def combine(paths):
        return [entry for path in paths for entry in get(path)]

    narrative = combine(fragments["narrative"])
    scenes = combine(fragments["scenes"])
    narrative_order = manifest["narrative_order"]
    chapters = get(manifest["chapters"])
    chapter_order = manifest["chapter_order"]
    memory_manifest = manifest.get("memories")
    memories = get(memory_manifest["entries"]) if memory_manifest else []
    project = {
        "manifest_version": manifest["version"],
        "narrative": narrative,
        "scenes": scenes,
        "beats": get(manifest["beats"]),
        "assets": get(manifest["assets"]),
        "editions": {lang: combine(fragments["translations"][lang]) for lang in LANGUAGES},
        "ui": {lang: get(manifest["ui"][lang]) for lang in LANGUAGES},
        "narrative_order": narrative_order,
        "narrative_index": {narrative_id: index for index, narrative_id in enumerate(narrative_order)},
        "narrative_by_id": {entry["id"]: entry for entry in narrative},
        "chapters": chapters,
        "chapter_order": chapter_order,
        "chapter_index": {chapter_id: index for index, chapter_id in enumerate(chapter_order)},
        "chapter_by_id": {chapter["id"]: chapter for chapter in chapters},
        "chapter_editions": {lang: get(manifest["chapter_translations"][lang]) for lang in LANGUAGES},
        "memories": memories,
        "memory_by_id": {entry["id"]: entry for entry in memories},
        "memory_editions": {lang: get(memory_manifest["translations"][lang]) if memory_manifest else {} for lang in LANGUAGES},
    }
    project["scene_by_id"] = {scene["id"]: scene for scene in scenes}
    project["narrative_to_scene"] = {entry["id"]: entry["scene"] for entry in narrative}
    project["narrative_to_chapter"] = {
        narrative_id: chapter["id"]
        for chapter in chapters
        for narrative_id in chapter["narrative_ids"]
    }
    project["frames_by_scene"] = {
        scene_id: resolve(project, scene_id)
        for scene_id in project["scene_by_id"]
    }
    project["frame_index_by_narrative"] = {
        frame["id"]: index
        for frames in project["frames_by_scene"].values()
        for index, frame in enumerate(frames)
    }
    return project

def canonical_furthest_id(furthest_id, seen_ids, narrative_index):
    """Finds the furthest still-valid stable ID using current canonical order."""
    candidates = set(seen_ids)
    if furthest_id:
        candidates.add(furthest_id)
    valid = [narrative_id for narrative_id in candidates if narrative_id in narrative_index]
    return max(valid, key=narrative_index.__getitem__) if valid else None

def memory_unlocks(condition, seen_ids, seen_scenes, unlocked_chapters):
    if "seen_id" in condition:
        return condition["seen_id"] in seen_ids
    if "seen_scene" in condition:
        return condition["seen_scene"] in seen_scenes
    if "chapter" in condition:
        return condition["chapter"] in unlocked_chapters
    return False

def advance_progress(seen_ids, furthest_id, narrative_id, narrative_index):
    """Returns seen content and furthest stable ID using canonical data order."""
    updated_seen_ids = set(seen_ids)
    updated_seen_ids.add(narrative_id)
    return updated_seen_ids, canonical_furthest_id(furthest_id, updated_seen_ids, narrative_index)

def chapter_for_narrative(project, narrative_id):
    return project["narrative_to_chapter"][narrative_id]

def unlocked_chapters(project, furthest_position):
    if furthest_position < 0:
        return set()
    return {
        chapter["id"]
        for chapter in project["chapters"]
        if project["narrative_index"][chapter["first_narrative_id"]] <= furthest_position
    }

def merge(state, delta):
    result = copy.deepcopy(state)
    for key, value in delta.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result

def resolve(project, scene_id):
    scene = project.get("scene_by_id", {}).get(scene_id)
    if scene is None:
        scene = next(s for s in project["scenes"] if s["id"] == scene_id)
    state = copy.deepcopy(scene["defaults"])
    frames = []
    for event in scene["sequence"]:
        if "dialogue" in event:
            frames.append({"id": event["dialogue"], "state": copy.deepcopy(state)})
        elif "beat" in event:
            state = merge(state, project["beats"][event["beat"]])
        else:
            state = merge(state, event)
    return frames

def validate(project, root):
    errors = []
    def check_unique(items, label):
        seen = set()
        for item in items:
            key = item.get("id")
            if not key or key in seen:
                errors.append("duplicate/empty " + label + ": " + str(key))
            seen.add(key)
        return seen
    def validate_unlock(condition, label):
        if not isinstance(condition, dict) or len(condition) != 1:
            errors.append("invalid unlock condition: " + label)
            return
        key, value = next(iter(condition.items()))
        if key == "seen_id" and value not in ids:
            errors.append("invalid seen_id unlock: " + label)
        elif key == "seen_scene" and value not in scenes:
            errors.append("invalid seen_scene unlock: " + label)
        elif key == "chapter" and value not in chapters:
            errors.append("invalid chapter unlock: " + label)
        elif key not in {"seen_id", "seen_scene", "chapter"}:
            errors.append("invalid unlock condition: " + label)
    ids = check_unique(project["narrative"], "narrative ID")
    scenes = check_unique(project["scenes"], "scene ID")
    chapters = check_unique(project["chapters"], "chapter ID")
    memory_ids = check_unique(project["memories"], "memory ID")
    order = project["narrative_order"]
    order_ids = check_unique([{"id": narrative_id} for narrative_id in order], "narrative order ID")
    for key in sorted(ids - order_ids):
        errors.append("missing canonical order: " + key)
    for key in sorted(order_ids - ids):
        errors.append("unknown canonical order ID: " + key)
    chapter_order_ids = check_unique([{"id": chapter_id} for chapter_id in project["chapter_order"]], "chapter order ID")
    for key in sorted(chapters - chapter_order_ids):
        errors.append("missing canonical chapter order: " + key)
    for key in sorted(chapter_order_ids - chapters):
        errors.append("unknown canonical chapter order ID: " + key)
    chapter_narratives = set()
    for chapter in project["chapters"]:
        chapter_id = chapter["id"]
        required = ("arc_id", "order", "first_narrative_id", "narrative_ids", "scenes")
        if any(key not in chapter for key in required):
            errors.append("malformed chapter: " + chapter_id)
            continue
        if not chapter["narrative_ids"] or chapter["first_narrative_id"] != chapter["narrative_ids"][0]:
            errors.append("invalid chapter start: " + chapter_id)
        for narrative_id in chapter["narrative_ids"]:
            if narrative_id not in ids:
                errors.append("invalid chapter narrative: " + narrative_id)
            elif narrative_id in chapter_narratives:
                errors.append("narrative belongs to multiple chapters: " + narrative_id)
            chapter_narratives.add(narrative_id)
        for scene_id in chapter["scenes"]:
            if scene_id not in scenes:
                errors.append("invalid chapter scene: " + scene_id)
    for narrative_id in sorted(ids - chapter_narratives):
        errors.append("narrative missing chapter: " + narrative_id)
    for lang in LANGUAGES:
        localized_chapters = project["chapter_editions"][lang]
        for chapter_id in chapters:
            if chapter_id not in localized_chapters:
                errors.append("missing " + lang + " chapter: " + chapter_id)
        for chapter_id, metadata in localized_chapters.items():
            if chapter_id not in chapters:
                errors.append("unknown localized chapter: " + chapter_id)
            elif not all(str(metadata.get(key, "")).strip() for key in ("arc", "chapter", "title", "location")):
                errors.append("empty " + lang + " chapter metadata: " + chapter_id)
    for lang in LANGUAGES:
        edition = project["editions"][lang]
        localized = check_unique(edition, lang + " ID")
        for key in sorted(ids - localized):
            errors.append("missing " + lang + ": " + key)
        for entry in edition:
            if not entry.get("text", "").strip():
                errors.append("empty " + lang + ": " + entry["id"])
            if entry["id"] not in ids:
                errors.append("unknown localized ID: " + entry["id"])
    if set(project["ui"]["en"]) != set(project["ui"]["pt_BR"]):
        errors.append("UI edition keys do not align")
    for entry in project["narrative"]:
        if entry.get("scene") not in scenes:
            errors.append("invalid scene reference: " + str(entry.get("scene")))
    refs = []
    for scene in project["scenes"]:
        for event in scene["sequence"]:
            if "beat" in event and event["beat"] not in project["beats"]:
                errors.append("invalid beat: " + event["beat"])
            if "dialogue" in event:
                refs.append(event["dialogue"])
                if event["dialogue"] not in ids:
                    errors.append("invalid narrative reference: " + event["dialogue"])
                elif next(n for n in project["narrative"] if n["id"] == event["dialogue"])["scene"] != scene["id"]:
                    errors.append("narrative belongs to another scene: " + event["dialogue"])
        if any("beat" in e and e["beat"] not in project["beats"] for e in scene["sequence"]):
            continue
        for frame in resolve(project, scene["id"]):
            state = frame["state"]
            for kind in ("background", "music", "ambience"):
                ref = state.get(kind)
                if ref is not None and ref not in project["assets"].get(kind, {}):
                    errors.append("invalid " + kind + ": " + ref)
            if state.get("animation") not in ("none", "subtle"):
                errors.append("invalid animation")
    for key in ids:
        if refs.count(key) != 1:
            errors.append("unreachable/repeated narrative: " + key)
    for kind, assets in project["assets"].items():
        for path in assets.values():
            if not (Path(root) / path).is_file():
                errors.append("missing asset: " + path)
    allowed_categories = {"illustrations", "characters", "scenes", "death_memories"}
    fact_ids = set()
    for memory in project["memories"]:
        memory_id = memory["id"]
        if memory.get("category") not in allowed_categories:
            errors.append("invalid memory category: " + memory_id)
        if memory.get("chapter_id") not in chapters:
            errors.append("invalid memory chapter: " + memory_id)
        validate_unlock(memory.get("unlock"), "memory: " + memory_id)
        if memory.get("asset") and not (Path(root) / memory["asset"]).is_file():
            errors.append("missing memory asset: " + memory_id)
        if memory.get("category") in {"scenes", "death_memories"}:
            start, end = memory.get("replay_start_id"), memory.get("replay_end_id")
            if start not in ids or end not in ids or project["narrative_index"].get(start, 0) > project["narrative_index"].get(end, -1):
                errors.append("invalid memory replay target: " + memory_id)
        if memory.get("category") == "characters":
            if memory.get("first_narrative_id") not in ids:
                errors.append("invalid memory character: " + memory_id)
            for fact in memory.get("facts", []):
                fact_id = fact.get("id")
                if not fact_id or fact_id in fact_ids:
                    errors.append("invalid memory fact: " + memory_id)
                fact_ids.add(fact_id)
                validate_unlock(fact.get("unlock"), "fact: " + str(fact_id))
        for lang in LANGUAGES:
            localized = project["memory_editions"][lang]
            if memory_id not in localized:
                errors.append("missing " + lang + " memory: " + memory_id)
                continue
            metadata = localized[memory_id]
            fields = ("name", "description") if memory.get("category") == "characters" else ("title", "description")
            if any(not str(metadata.get(field, "")).strip() for field in fields):
                errors.append("incomplete " + lang + " memory metadata: " + memory_id)
            for fact in memory.get("facts", []):
                fact_id = fact.get("id")
                if fact_id not in localized:
                    errors.append("missing " + lang + " memory fact: " + str(fact_id))
                elif not str(localized[fact_id].get("text", "")).strip():
                    errors.append("incomplete " + lang + " memory fact: " + fact_id)
    return errors
