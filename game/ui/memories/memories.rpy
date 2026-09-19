screen memories():
    tag menu
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 20
        text ui_text("memories") size 52 color "#e1bd82"
        textbutton ui_text("illustrations") action ShowMenu("memory_category", category="illustrations")
        textbutton ui_text("characters") action ShowMenu("memory_category", category="characters")
        textbutton ui_text("scenes") action ShowMenu("memory_category", category="scenes")
        textbutton ui_text("death_memories") action ShowMenu("memory_category", category="death_memories")
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()

screen memory_category(category):
    tag menu
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 16
        text ui_text(category) size 48 color "#e1bd82"
        for entry in memory_entries(category):
            $ metadata = memory_metadata(entry["id"])
            if category == "characters":
                textbutton metadata["name"] action ShowMenu("memory_character", memory_id=entry["id"])
            elif category == "illustrations":
                textbutton metadata["title"] action ShowMenu("memory_illustration", memory_id=entry["id"])
            else:
                textbutton metadata["title"] action [SetVariable("memory_replay_target", entry["id"]), Jump("memory_replay_start")]
        textbutton ui_text("back") action ShowMenu("memories")
    key "game_menu" action ShowMenu("memories")

screen memory_illustration(memory_id):
    tag menu
    $ entry = project_data["memory_by_id"][memory_id]
    $ metadata = memory_metadata(memory_id)
    add entry["asset"]
    add Solid("#07101b55")
    vbox:
        align (0.5, 0.88)
        text metadata["title"] size 42 color "#f3eee3" xalign 0.5
        text metadata["description"] size 24 color "#d7dce3" xalign 0.5
    imagebutton:
        idle "assets/overlays/eye.png"
        hover "assets/overlays/eye_hover.png"
        xpos 1832
        ypos 30
        action HideInterface()
        alt ui_text("hide")
    textbutton ui_text("back") xpos 60 ypos 980 action ShowMenu("memory_category", category="illustrations")

screen memory_character(memory_id):
    tag menu
    use menu_background
    $ entry = project_data["memory_by_id"][memory_id]
    $ metadata = memory_metadata(memory_id)
    hbox:
        align (0.5, 0.5)
        spacing 52
        add entry["asset"] xysize (700, 394)
        vbox:
            xsize 620
            spacing 18
            text metadata["name"] size 52 color "#e1bd82"
            text metadata["description"] size 26
            text ui_text("facts") size 25 color "#d2b682"
            for fact in unlocked_memory_facts(memory_id):
                text memory_metadata(fact["id"])["text"] size 23
            textbutton ui_text("back") action ShowMenu("memory_category", category="characters")
    key "game_menu" action ShowMenu("memory_category", category="characters")
