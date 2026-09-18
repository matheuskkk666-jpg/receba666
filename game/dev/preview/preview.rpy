init python:
    import os
    def preview_scene():
        scene = os.environ.get("LN_PREVIEW_SCENE", "test_observatory")
        if scene not in [s["id"] for s in project_data["scenes"]]:
            raise Exception("Unknown preview scene: " + scene)
        return scene
    def preview_index():
        target = os.environ.get("LN_PREVIEW_ID")
        if not target:
            return 0
        return next(i for i, f in enumerate(frames) if f["id"] == target)

label before_main_menu:
    python:
        if os.environ.get("LN_PREVIEW_LANGUAGE") in ("pt_BR", "en"):
            persistent.edition = os.environ["LN_PREVIEW_LANGUAGE"]
        if os.environ.get("LN_PREVIEW_MODE") in ("static", "cinematic"):
            persistent.presentation = os.environ["LN_PREVIEW_MODE"]
    if os.environ.get("LN_PREVIEW_SCENE") and not renpy.session.get("preview_launched"):
        $ renpy.session["preview_launched"] = True
        $ renpy.run(Start())
    return
