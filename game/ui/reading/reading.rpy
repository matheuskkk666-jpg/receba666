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
            text localized_entry().get("speaker", "") style "say_label" id "who"
            text localized_entry()["text"] style "say_dialogue" id "what"
    add Solid("#bda576", xsize=1440, ysize=2) xpos 240 ypos 755
    imagebutton:
        id "hide_ui"
        idle "assets/overlays/eye.png"
        hover "assets/overlays/eye_hover.png"
        xpos 1832
        ypos 30
        action HideInterface()
        alt ui_text("hide")

screen choice(items):
    # Required engine hook; narrative choices are intentionally unsupported.
    pass
