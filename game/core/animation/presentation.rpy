transform scene_static_wide:
    subpixel True
    align (0.5, 0.5)

transform scene_static_low:
    subpixel True
    align (0.5, 0.62)
    zoom 1.05

transform scene_static_detail:
    subpixel True
    align (0.54, 0.66)
    zoom 1.11

transform scene_static_close:
    subpixel True
    align (0.5, 0.64)
    zoom 1.08

transform scene_motion_wide:
    subpixel True
    align (0.5, 0.5)
    zoom 1.015
    ease 24.0 zoom 1.055
    ease 24.0 zoom 1.015
    repeat

transform scene_motion_low:
    subpixel True
    align (0.5, 0.62)
    zoom 1.05
    ease 22.0 zoom 1.085
    ease 22.0 zoom 1.05
    repeat

transform scene_motion_detail:
    subpixel True
    align (0.54, 0.66)
    zoom 1.11
    ease 20.0 align (0.51, 0.64) zoom 1.14
    ease 20.0 align (0.54, 0.66) zoom 1.11
    repeat

transform scene_motion_close:
    subpixel True
    align (0.5, 0.64)
    zoom 1.08
    ease 24.0 zoom 1.115
    ease 24.0 zoom 1.08
    repeat

init python:
    def visual_asset_path(slot):
        """Use a final asset when present, otherwise its explicit dev placeholder."""
        if renpy.loadable(slot["path"]):
            return slot["path"]
        placeholder = slot.get("development_placeholder")
        if placeholder and renpy.loadable(placeholder):
            return placeholder
        raise Exception("No renderable asset for " + slot["asset_type"] + ":" + slot["id"])

    def scene_visual_assets(state):
        slots = resolve_scene_visual_slots(project_data, state)
        return {
            "background": visual_asset_path(slots["background"]),
            "foreground": visual_asset_path(slots["foreground"]) if slots["foreground"] else None,
        }

screen scene_visual(art, shot):
    if persistent.presentation == "cinematic" and director_state.get("animation", "subtle") != "none":
        if shot == "low":
            add art at scene_motion_low
        elif shot == "detail":
            add art at scene_motion_detail
        elif shot == "close":
            add art at scene_motion_close
        else:
            add art at scene_motion_wide
    else:
        if shot == "low":
            add art at scene_static_low
        elif shot == "detail":
            add art at scene_static_detail
        elif shot == "close":
            add art at scene_static_close
        else:
            add art at scene_static_wide

screen scene_art():
    zorder 10
    $ assets = scene_visual_assets(director_state)
    $ shot = director_state.get("shot", "wide")
    use scene_visual(assets["background"], shot)
    if assets["foreground"]:
        use scene_visual(assets["foreground"], shot)
    add Solid(director_state.get("lighting", "#00000000"))
