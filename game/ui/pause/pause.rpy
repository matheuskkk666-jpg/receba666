screen menu_background():
    if main_menu:
        add "assets/backgrounds/observatory.png"
    add Solid("#070e1bbf")

screen pause_menu():
    tag menu
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 14
        text ui_text("pause") size 52 color "#e1bd82" xalign 0.5
        null height 12
        textbutton ui_text("resume") action Return()
        textbutton ui_text("history") action ShowMenu("history")
        textbutton ui_text("save") action ShowMenu("save")
        textbutton ui_text("load") action ShowMenu("load")
        textbutton ui_text("chapters") action ShowMenu("chapters")
        textbutton ui_text("settings") action ShowMenu("settings")
        textbutton ui_text("main") action Confirm(ui_text("confirm"), [Function(controlled_menu_exit), MainMenu(confirm=False)], Return())
    key "game_menu" action Return()
