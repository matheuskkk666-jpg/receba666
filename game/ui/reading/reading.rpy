screen say(who, what):
    window:
        id "window"
        xalign 0.5
        ypos 755
        yanchor 0.0
        xsize 1440
        ysize 245
        background Solid("#0b1429e6")
        padding (52, 28)
        vbox:
            spacing 15
            text presentation_speaker() style "say_label" id "who"
            text what style "say_dialogue" id "what"
    add Solid("#bda576", xsize=1440, ysize=2) xpos 240 ypos 755
    imagebutton:
        id "hide_ui"
        idle "assets/overlays/eye.png"
        hover "assets/overlays/eye_hover.png"
        xpos 1832
        ypos 30
        action HideInterface()
        alt ui_text("hide")

screen journey_indicator(chapter_id):
    zorder 70
    $ metadata = chapter_metadata(chapter_id)
    frame:
        xpos 56
        ypos 52
        background Solid("#091326c8")
        padding (22, 14)
        vbox:
            spacing 5
            text "[metadata['arc']] — [metadata['location']]" size 20 color "#d2b682"
            text "[metadata['chapter']] — [metadata['title']]" size 26 color "#f3eee3"
    timer 4.0 action Hide("journey_indicator")

screen choice(items):
    # Required engine hook; narrative choices are intentionally unsupported.
    pass
