init -80 python:
    from foundation.model import advance_progress, canonical_furthest_id, chapter_for_narrative, load_project, memory_unlocks, resolve, unlocked_chapters
    def read_data(path):
        with renpy.open_file(path) as stream:
            return stream.read().decode("utf-8")
    project_data = load_project(config.gamedir, read_data)
    edition_index = {lang: {e["id"]: e for e in entries} for lang, entries in project_data["editions"].items()}
    chapter_edition_index = project_data["chapter_editions"]
    memory_edition_index = project_data["memory_editions"]
    def ui_text(key):
        return project_data["ui"][persistent.edition or "pt_BR"][key]
    def localized_entry():
        return edition_index[persistent.edition or "pt_BR"][current_id]
    def chapter_metadata(chapter_id):
        return chapter_edition_index[persistent.edition or "pt_BR"][chapter_id]
    def chapter_display_title(chapter_id):
        return chapter_metadata(chapter_id)["title"]
    def chapter_button_label(chapter_id):
        metadata = chapter_metadata(chapter_id)
        return metadata["chapter"] + " — " + metadata["title"]
    def slot_metadata(chapter_id, legacy_metadata=None):
        if chapter_id in project_data["chapter_by_id"]:
            return chapter_metadata(chapter_id)
        return legacy_metadata or {"arc": "", "chapter": "", "title": "", "location": ""}
    def memory_metadata(memory_id):
        return memory_edition_index[persistent.edition or "pt_BR"][memory_id]
    def set_edition(lang):
        persistent.edition = lang
        renpy.save_persistent()
        renpy.restart_interaction()

    def bind_history_id(entry):
        entry.narrative_id = current_id
    config.history_callbacks.append(bind_history_id)

    def history_entry(entry):
        key = getattr(entry, "narrative_id", None)
        return edition_index[persistent.edition].get(key, {"speaker": entry.who or "", "text": entry.what})

default persistent.edition = "pt_BR"
default persistent.presentation = "cinematic"
