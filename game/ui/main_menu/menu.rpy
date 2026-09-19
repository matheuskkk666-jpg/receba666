init python:
    def start_journey_action():
        return Start("journey_start")

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
        if has_resume_state():
            textbutton ui_text("continue") id "continue_journey" action Start("continue_journey") style "journey_primary_button"
            textbutton ui_text("start") id "start_journey" action Confirm(ui_text("restart_journey_confirm"), start_journey_action(), Return())
        else:
            textbutton ui_text("start") id "start_journey" action start_journey_action() style "journey_primary_button"
        if has_journey_progress():
            textbutton ui_text("chapters") id "journey_chapters" action ShowMenu("chapters")
        if has_memories():
            textbutton ui_text("memories") id "journey_memories" action ShowMenu("memories")
        textbutton ui_text("settings") action ShowMenu("settings")
        textbutton ui_text("exit") action Quit(confirm=False)

screen confirm(message, yes_action, no_action):
    modal True
    zorder 200
    add Solid("#050912e8")
    vbox:
        align (0.5, 0.5)
        spacing 24
        text message id "confirm_message" xmaximum 1000
        textbutton ui_text("yes") action yes_action
        textbutton ui_text("no") action no_action
    key "game_menu" action no_action
