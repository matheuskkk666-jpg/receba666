screen chapters():
    tag menu
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 30
        text ui_text("chapters") size 48 color "#e1bd82"
        text ui_text("shell") xmaximum 900
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()
