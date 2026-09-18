init -80 python:
    from foundation.model import load_project, resolve
    def read_data(path):
        with renpy.open_file(path) as stream:
            return stream.read().decode("utf-8")
    project_data = load_project(config.gamedir, read_data)
    edition_index = {lang: {e["id"]: e for e in entries} for lang, entries in project_data["editions"].items()}
    def ui_text(key):
        return project_data["ui"][persistent.edition or "pt_BR"][key]
    def localized_entry():
        return edition_index[persistent.edition or "pt_BR"][current_id]
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
