init -70 python:
    renpy.music.register_channel("ambience", mixer="music", loop=True)
    def apply_audio(state):
        for channel in ("music", "ambience"):
            ref = state.get(channel)
            path = project_data["assets"][channel].get(ref) if ref else None
            if path and renpy.music.get_playing(channel) != path:
                renpy.music.play(path, channel=channel, fadein=1.0)
            elif not path:
                renpy.music.stop(channel=channel, fadeout=0.5)
        renpy.music.set_volume(state.get("music_gain", 0.25), channel="music")
