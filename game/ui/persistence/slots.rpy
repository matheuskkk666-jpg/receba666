screen save():
    tag menu
    use file_slots("save")

screen load():
    tag menu
    use file_slots("load")

screen file_slots(kind):
    use menu_background
    vbox:
        align (0.5, 0.5)
        spacing 28
        text ui_text(kind) size 48 color "#e1bd82"
        grid 3 2:
            spacing 24
            for slot in range(1, 7):
                $ metadata = slot_metadata(FileJson(slot, "chapter_id", empty=None), {
                    "arc": FileJson(slot, "arc", empty="") or "",
                    "chapter": FileJson(slot, "chapter", empty="") or "",
                    "title": FileJson(slot, "chapter_title", empty="") or "",
                    "location": FileJson(slot, "location", empty="") or "",
                })
                button:
                    xsize 430
                    ysize 250
                    background Solid("#162437")
                    action (FileSave(slot, confirm=False) if kind == "save" else FileLoad(slot, confirm=False))
                    vbox:
                        spacing 8
                        add FileScreenshot(slot) xysize (384, 180)
                        text FileTime(slot, format="%d/%m/%Y · %H:%M", empty=ui_text("empty")) size 21
                        text "[metadata['arc']] · [metadata['chapter']]" size 18
                        text metadata["title"] id "slot_[slot]_title" size 19 color "#d2b682"
                        text metadata["location"] size 17 color "#bdc8d8"
        textbutton ui_text("back") action Return()
    key "game_menu" action Return()
