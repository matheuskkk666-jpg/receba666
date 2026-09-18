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
    return {
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
    }

def advance_progress(seen_ids, furthest_position, narrative_id, narrative_index):
    """Returns immutable-friendly progress updates using canonical data order."""
    updated_seen_ids = set(seen_ids)
    updated_seen_ids.add(narrative_id)
    return updated_seen_ids, max(furthest_position, narrative_index[narrative_id])

def chapter_for_narrative(project, narrative_id):
    for chapter in project["chapters"]:
        if narrative_id in chapter["narrative_ids"]:
            return chapter["id"]
    raise KeyError("narrative ID has no chapter: " + narrative_id)

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
    ids = check_unique(project["narrative"], "narrative ID")
    scenes = check_unique(project["scenes"], "scene ID")
    chapters = check_unique(project["chapters"], "chapter ID")
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
    return errors
