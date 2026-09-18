init python:
    # Reserved destinations, intentionally not displayed before implementation.
    future_menu_destinations = ("continue", "chapters", "memories")

label main_menu:
    call screen main_menu
    return

screen main_menu():
    tag menu
    add "assets/backgrounds/observatory.png"
    add Solid("#070d1ba6")
    vbox:
        xpos 220
        ypos 290
        spacing 18
        text ui_text("eyebrow") size 20 color "#d2b682" kerning 4
        text ui_text("title") size 76 color "#f3eee3"
        null height 42
        textbutton ui_text("start") action Start()
        textbutton ui_text("settings") action ShowMenu("settings")
        textbutton ui_text("exit") action Quit(confirm=False)

screen confirm(message, yes_action, no_action):
    modal True
    zorder 200
    add Solid("#050912e8")
    vbox:
        align (0.5, 0.5)
        spacing 24
        text ui_text("confirm") xmaximum 1000
        textbutton ui_text("yes") action yes_action
        textbutton ui_text("back") action no_action
    key "game_menu" action no_action
