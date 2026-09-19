import copy
import json
from pathlib import Path

LANGUAGES = ("pt_BR", "en")
PRESENTATION_KINDS = ("narration", "dialogue", "thought")
ART_CATEGORIES = ("Background", "Character/environment composition", "Hero CG")
REUSE_CLASSES = ("A", "B", "C", "D")

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
    presentation_manifest = manifest.get("presentation", {})
    presentation_documents = [get(path) for path in presentation_manifest.get("fragments", [])]
    art_plans = [get(path) for path in manifest.get("art_plans", [])]
    presentation_groups = [
        {"parent_id": narrative_id, "segments": segments}
        for document in presentation_documents
        for narrative_id, segments in document.get("narrative", {}).items()
    ]
    presentation_source_narrative = combine(presentation_manifest.get("narrative_sources", []))
    presentation_source_editions = {
        lang: combine(presentation_manifest.get("translation_sources", {}).get(lang, []))
        for lang in LANGUAGES
    }
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
        "presentation_groups": presentation_groups,
        "presentation_required_ids": presentation_manifest.get("required_narrative_ids", []),
        "presentation_speakers": set(presentation_manifest.get("speakers", [])),
        "art_plans": art_plans,
    }
    project["presentation_parent_by_id"] = {
        entry["id"]: entry for entry in narrative + presentation_source_narrative
    }
    project["presentation_editions"] = {}
    project["presentation_translation_by_language"] = {}
    for lang in LANGUAGES:
        rows = project["editions"][lang] + presentation_source_editions[lang]
        project["presentation_editions"][lang] = rows
        project["presentation_translation_by_language"][lang] = {
            entry["id"]: entry for entry in rows
        }
    project["presentation_by_narrative"] = {
        group["parent_id"]: group["segments"] for group in presentation_groups
    }
    project["presentation_segment_by_id"] = {
        segment["id"]: segment
        for group in presentation_groups
        for segment in group["segments"]
    }
    project["art_requirement_by_id"] = {
        requirement["asset_id"]: requirement
        for plan in art_plans
        for requirement in plan.get("requirements", [])
    }
    project["art_character_by_id"] = {
        character["id"]: character
        for plan in art_plans
        for character in plan.get("characters", [])
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

def presentation_for(project, narrative_id):
    """Returns explicit segments or a transient whole-row compatibility segment."""
    explicit = project["presentation_by_narrative"].get(narrative_id)
    if explicit is not None:
        return explicit
    parent = project["presentation_parent_by_id"].get(narrative_id)
    if parent is None:
        raise KeyError(narrative_id)
    ranges = {}
    for lang in LANGUAGES:
        row = project["presentation_translation_by_language"][lang].get(narrative_id)
        if row is None:
            raise KeyError(narrative_id + ":" + lang)
        ranges[lang] = {"start": 0, "end": len(row["text"])}
    return [{
        "id": narrative_id + ".p000",
        "kind": parent.get("kind", "narration"),
        "speaker": None,
        "ranges": ranges,
        "synthetic": True,
    }]

def presentation_segment(project, narrative_id, segment_id):
    for index, segment in enumerate(presentation_for(project, narrative_id)):
        if segment["id"] == segment_id:
            result = copy.deepcopy(segment)
            result["parent_id"] = narrative_id
            result["ordinal"] = index
            return result
    raise KeyError(segment_id)

def resolve_presentation_text(project, narrative_id, segment_id, language, display=False):
    if language not in LANGUAGES:
        raise KeyError(language)
    segment = presentation_segment(project, narrative_id, segment_id)
    bounds = segment["ranges"][language]
    row = project["presentation_translation_by_language"][language][narrative_id]
    text = row["text"][bounds["start"]:bounds["end"]]
    return text.strip() if display else text

def resolve_presentation_direction(project, narrative_id, segment_id):
    """Resolve scene → canonical frame → beat → presentation override."""
    scene_id = project["narrative_to_scene"][narrative_id]
    frame_index = project["frame_index_by_narrative"][narrative_id]
    state = copy.deepcopy(project["frames_by_scene"][scene_id][frame_index]["state"])
    segment = presentation_segment(project, narrative_id, segment_id)
    beat = segment.get("beat")
    if beat:
        state = merge(state, project["beats"][beat])
    state = merge(state, segment.get("direction", {}))
    return state

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
    presentation_parents = set(project["presentation_parent_by_id"])
    presentation_parent_ids = check_unique(
        [{"id": group["parent_id"]} for group in project["presentation_groups"]],
        "presentation parent ID",
    )
    segment_ids = set()
    for group in project["presentation_groups"]:
        parent_id = group["parent_id"]
        if parent_id not in presentation_parents:
            errors.append("unknown presentation parent: " + parent_id)
            continue
        segments = group.get("segments")
        if not isinstance(segments, list) or not segments:
            errors.append("missing presentation segments: " + parent_id)
            continue
        for segment in segments:
            segment_id = segment.get("id")
            if not segment_id or segment_id in segment_ids:
                errors.append("duplicate/empty presentation segment ID: " + str(segment_id))
            segment_ids.add(segment_id)
            if segment.get("kind") not in PRESENTATION_KINDS:
                errors.append("invalid presentation kind: " + str(segment_id))
            beat = segment.get("beat")
            if beat is not None and beat not in project["beats"]:
                errors.append("invalid presentation beat: " + str(segment_id))
            direction = segment.get("direction", {})
            if not isinstance(direction, dict):
                errors.append("invalid presentation direction: " + str(segment_id))
            else:
                composition_id = direction.get("composition_id")
                if composition_id is not None and composition_id not in project["art_requirement_by_id"]:
                    errors.append("invalid presentation composition: " + str(segment_id))
                elif composition_id is not None and segment_id not in project["art_requirement_by_id"][composition_id].get("presentation_segments", []):
                    errors.append("presentation composition lacks coverage: " + str(segment_id))
                for kind in ("background", "music", "ambience"):
                    ref = direction.get(kind)
                    if ref is not None and ref not in project["assets"].get(kind, {}):
                        errors.append("invalid presentation " + kind + ": " + str(segment_id))
            speaker = segment.get("speaker")
            if speaker is not None and speaker not in project["presentation_speakers"]:
                errors.append("invalid presentation speaker: " + str(segment_id))
        for lang in LANGUAGES:
            row = project["presentation_translation_by_language"][lang].get(parent_id)
            if row is None:
                errors.append("missing " + lang + " presentation translation: " + parent_id)
                continue
            cursor = 0
            text_length = len(row.get("text", ""))
            for segment in segments:
                segment_id = str(segment.get("id"))
                bounds = segment.get("ranges", {}).get(lang)
                if not isinstance(bounds, dict):
                    errors.append("missing " + lang + " presentation range: " + segment_id)
                    continue
                start, end = bounds.get("start"), bounds.get("end")
                if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > text_length:
                    errors.append("invalid " + lang + " presentation range: " + segment_id)
                    continue
                if start < cursor:
                    errors.append("overlapping " + lang + " presentation range: " + segment_id)
                elif start > cursor:
                    errors.append("gap in " + lang + " presentation before: " + segment_id)
                cursor = max(cursor, end)
            if cursor != text_length:
                errors.append("incomplete " + lang + " presentation coverage: " + parent_id)
    for parent_id in project["presentation_required_ids"]:
        if parent_id not in presentation_parent_ids:
            errors.append("missing explicit presentation: " + parent_id)
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
    art_requirement_ids = set()
    art_character_ids = set()
    for plan in project["art_plans"]:
        plan_id = str(plan.get("id", ""))
        plan_scenes = plan.get("scenes", [])
        for scene_id in plan_scenes:
            if scene_id not in scenes:
                errors.append("invalid art plan scene: " + plan_id)
        for character in plan.get("characters", []):
            character_id = character.get("id")
            if not character_id or character_id in art_character_ids:
                errors.append("duplicate/empty art character ID: " + str(character_id))
            art_character_ids.add(character_id)
            threshold = character.get("disclosure_threshold")
            if threshold is not None and threshold not in segment_ids:
                errors.append("invalid art character disclosure: " + str(character_id))
        for requirement in plan.get("requirements", []):
            asset_id = requirement.get("asset_id")
            if not asset_id or asset_id in art_requirement_ids:
                errors.append("duplicate/empty art requirement ID: " + str(asset_id))
            art_requirement_ids.add(asset_id)
            if requirement.get("category") not in ART_CATEGORIES:
                errors.append("invalid art requirement category: " + str(asset_id))
            if requirement.get("reuse_class") not in REUSE_CLASSES:
                errors.append("invalid art reuse class: " + str(asset_id))
            if not requirement.get("static"):
                errors.append("missing Static art plan: " + str(asset_id))
            if not requirement.get("cinematic"):
                errors.append("missing Cinematic art plan: " + str(asset_id))
            generation = requirement.get("generation_spec", {})
            if any(not generation.get(field) for field in ("canvas", "safe_ui", "depth_layers", "continuity", "do_not_show")):
                errors.append("incomplete generation spec: " + str(asset_id))
            for scene_id in requirement.get("scenes", []):
                if scene_id not in scenes:
                    errors.append("invalid art requirement scene: " + str(asset_id))
            for presentation_id in requirement.get("presentation_segments", []):
                if presentation_id not in segment_ids:
                    errors.append("invalid art presentation reference: " + str(asset_id))
            for character_id in requirement.get("characters", []):
                if character_id not in project["art_character_by_id"]:
                    errors.append("invalid art character reference: " + str(asset_id))
            reuse_of = requirement.get("reuse_of")
            if reuse_of is not None and reuse_of not in project["art_requirement_by_id"]:
                errors.append("invalid art reuse reference: " + str(asset_id))
            hero_candidate = requirement.get("hero_candidate", False)
            if bool(hero_candidate) != (requirement.get("category") == "Hero CG"):
                errors.append("invalid Hero CG reference: " + str(asset_id))
        covered = {
            presentation_id
            for requirement in plan.get("requirements", [])
            for presentation_id in requirement.get("presentation_segments", [])
        }
        expected = {
            segment["id"]
            for scene_id in plan_scenes
            for frame in project["frames_by_scene"].get(scene_id, [])
            for segment in presentation_for(project, frame["id"])
        }
        for presentation_id in sorted(expected - covered):
            errors.append("presentation missing art coverage: " + presentation_id)
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
