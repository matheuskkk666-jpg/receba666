label start:
    $ enter_scene(preview_scene())
    $ frame_index = preview_index()
    show screen scene_art onlayer master
    while frame_index < len(frames):
        $ enter_frame(frame_index)
        $ reader(localized_entry().get("text", ""))
        $ frame_index += 1
    hide screen scene_art onlayer master
    $ renpy.music.stop(channel="music", fadeout=1.0)
    $ renpy.music.stop(channel="ambience", fadeout=1.0)
    return
