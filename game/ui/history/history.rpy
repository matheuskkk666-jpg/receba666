screen history():
    tag menu
    use menu_background
    vbox:
        xpos 300
        ypos 110
        spacing 25
        text ui_text("history") size 48 color "#e1bd82"
        viewport:
            xsize 1320
            ysize 720
            mousewheel True
            draggable True
            arrowkeys True
            vbox:
                spacing 28
                for item in _history_list:
                    $ entry = history_entry(item)
                    vbox:
                        spacing 8
                        if entry["speaker"]:
                            text entry["speaker"] style "say_label"
                        text entry["text"] size 28 xmaximum 1280 substitute False
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()
