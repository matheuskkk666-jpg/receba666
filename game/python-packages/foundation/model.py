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

    narrative_order = manifest["narrative_order"]
    return {
        "manifest_version": manifest["version"],
        "narrative": combine(fragments["narrative"]),
        "scenes": combine(fragments["scenes"]),
        "beats": get(manifest["beats"]),
        "assets": get(manifest["assets"]),
        "editions": {lang: combine(fragments["translations"][lang]) for lang in LANGUAGES},
        "ui": {lang: get(manifest["ui"][lang]) for lang in LANGUAGES},
        "narrative_order": narrative_order,
        "narrative_index": {narrative_id: index for index, narrative_id in enumerate(narrative_order)},
    }

def advance_progress(seen_ids, furthest_position, narrative_id, narrative_index):
    """Returns immutable-friendly progress updates using canonical data order."""
    updated_seen_ids = set(seen_ids)
    updated_seen_ids.add(narrative_id)
    return updated_seen_ids, max(furthest_position, narrative_index[narrative_id])

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
    order = project["narrative_order"]
    order_ids = check_unique([{"id": narrative_id} for narrative_id in order], "narrative order ID")
    for key in sorted(ids - order_ids):
        errors.append("missing canonical order: " + key)
    for key in sorted(order_ids - ids):
        errors.append("unknown canonical order ID: " + key)
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
