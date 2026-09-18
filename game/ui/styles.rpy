init -60:
    style default:
        font "DejaVuSans.ttf"
        size 30
        color "#e9e4db"
    style button:
        padding (20, 12)
        background None
        hover_background Solid("#bed8e514")
    style button_text:
        size 30
        idle_color "#c6cdd3"
        hover_color "#ffffff"
        selected_color "#e2bd7d"
        insensitive_color "#6e7886"
    style journey_primary_button is button:
        background Solid("#8b6a38")
        hover_background Solid("#b08a4c")
    style journey_primary_button_text is button_text:
        color "#fff8e9"
    style say_dialogue:
        font "DejaVuSans.ttf"
        size 34
        line_spacing 12
        color "#f1ece2"
    style say_label:
        size 25
        color "#e4bf81"
    style slider:
        xsize 540
        ysize 28
        left_bar Solid("#d6b47b")
        right_bar Solid("#3c4b5c")
        thumb Solid("#eee9df", xsize=14, ysize=28)
