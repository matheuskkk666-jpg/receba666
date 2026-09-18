screen settings():
    tag menu
    use menu_background
    vbox:
        xpos 460
        ypos 180
        spacing 22
        text ui_text("settings") size 52 color "#e1bd82"
        text ui_text("language")
        hbox:
            spacing 35
            textbutton "Português (Brasil)" action Function(set_edition, "pt_BR") selected persistent.edition == "pt_BR"
            textbutton "English" action Function(set_edition, "en") selected persistent.edition == "en"
        text ui_text("presentation")
        hbox:
            spacing 35
            textbutton ui_text("static") action Function(set_presentation, "static") selected persistent.presentation == "static"
            textbutton ui_text("cinematic") action Function(set_presentation, "cinematic") selected persistent.presentation == "cinematic"
        text ui_text("speed")
        bar value Preference("text speed") style "slider"
        text ui_text("volume")
        bar value Preference("music volume") style "slider"
        hbox:
            spacing 35
            textbutton ui_text("window") action Preference("display", "window")
            textbutton ui_text("fullscreen") action Preference("display", "fullscreen")
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()
