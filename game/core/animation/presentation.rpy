transform scene_motion:
    subpixel True
    align (0.5, 0.5)
    zoom 1.015
    ease 24.0 zoom 1.055
    ease 24.0 zoom 1.015
    repeat

screen scene_art():
    zorder 10
    $ art = project_data["assets"]["background"][director_state.get("background", "observatory")]
    if persistent.presentation == "cinematic" and director_state.get("animation", "subtle") != "none":
        add art at scene_motion
    else:
        add art
    add Solid(director_state.get("lighting", "#00000000"))
