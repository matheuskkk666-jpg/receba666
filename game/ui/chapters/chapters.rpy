screen chapters():
    tag menu
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 20
        text ui_text("chapters") size 48 color "#e1bd82"
        for chapter_id in project_data["chapter_order"]:
            if is_chapter_unlocked(chapter_id):
                $ metadata = chapter_metadata(chapter_id)
                textbutton chapter_button_label(chapter_id) id "chapter_[chapter_id]" action [SetVariable("chapter_navigation_target", chapter_id), Jump("chapter_start")]
            else:
                text ui_text("locked_chapter") id "locked_[chapter_id]" color "#8f96a5"
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()

screen chapter_card(chapter_id):
    zorder 80
    add Solid("#07101bdc")
    $ metadata = chapter_metadata(chapter_id)
    vbox:
        align (0.5, 0.5)
        spacing 16
        text metadata["arc"] size 24 color "#d2b682" xalign 0.5
        text metadata["chapter"] size 34 color "#f3eee3" xalign 0.5
        text metadata["title"] size 64 color "#f3eee3" xalign 0.5
        text metadata["location"] size 23 color "#bdc8d8" xalign 0.5

label chapter_opening:
    show screen chapter_card(current_chapter)
    with Dissolve(0.35)
    pause 2.2
    hide screen chapter_card
    with Dissolve(0.35)
    return
