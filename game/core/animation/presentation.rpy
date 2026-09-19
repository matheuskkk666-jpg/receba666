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

screen scene_art():
    zorder 10
    $ art = project_data["assets"]["background"][director_state.get("background", "observatory")]
    $ shot = director_state.get("shot", "wide")
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
    add Solid(director_state.get("lighting", "#00000000"))
