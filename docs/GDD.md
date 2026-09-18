# Game Design Document

## Product statement
A cinematic interactive-light-novel adaptation experience. The user primarily reads and advances. Presentation enhances the source through illustration, music, ambience, sound design, camera direction, subtle animation, and editorial UI.

Priority order:
**story > art > atmosphere > animation > interface > mechanics**

## Core experience
- Linear reading.
- No narrative choices.
- No QTE.
- No combat.
- No exploration layer.
- First click while text is typing completes the current text.
- Next click advances exactly one narrative unit.
- Text speed is configurable.
- Autoplay is optional.

## Target
- Windows first.
- Ren'Py.
- 1920x1080.
- 16:9 only as the authored composition.
- Mouse + keyboard.

## Languages
Portuguese and English are first-class independent editions.
Shared narrative IDs bind equivalent positions across languages.
Language may be switched during a scene without restarting it.
Each edition may retain its own terminology choices.

## Text presentation
### Dialogue
- speaker name visible;
- elegant centered lower-middle dialogue box;
- readable serif-oriented typography;
- translucent dark glass / subtle local blur;
- restrained ornaments.

### Thoughts
- same design language, visually more inward/intimate;
- may shift slightly toward the center;
- no excessive gimmicks.

### Narration
- ordinary narration uses the primary reading presentation;
- strong introspective passages may temporarily use a more literary centered treatment with the art slightly dimmed.

No narrative content is removed merely because the artwork depicts the same information.

## HUD
During normal reading:
- artwork occupies the full frame;
- no permanent bottom bar;
- a very small icon-only hide-UI control may remain at the upper-right.

At scene/chapter entry, upper-left temporary information may show:
- Arc / location;
- current chapter title from the selected edition.
It fades away after a short time.

## Pause menu
ESC dims/blurs the current scene and opens:
- Continue
- History
- Save
- Load
- Chapters
- Settings
- Main Menu

## Main menu
Before progress:
- Start Journey
- Settings
- Exit

With progress:
- Continue
- Start Journey
- Chapters
- Memories
- Settings
- Exit

Continue is the visual primary action when progress exists.

## Save behavior
- autosave at safe intervals, scene/chapter boundaries, checkpoint transitions, and controlled exits;
- manual save slots;
- continue returns to the most recent appropriate state;
- save metadata should include arc, chapter, location, timestamp, thumbnail, and playtime where practical.

## History
History is for rereading.
The player may temporarily inspect previous lines without destroying current progress.
Definitive repositioning should use chapter navigation or save/load.

## Chapters
- only reached chapters are selectable;
- future chapter titles are hidden;
- reached chapters may be restarted.

## Memories
Optional archive, never a collection grind.

### Illustrations
Important seen CGs/compositions can be viewed full-screen.
Future images remain hidden.

### Characters
Only characters already encountered.
Only information already learned in the story.
No wiki-derived future facts.

### Scenes
Important previously seen scenes can be replayed.

### Death Memories
Previously experienced deaths / Return by Death sequences can be replayed.
No hints about future deaths.

## Art direction
Hybrid style:
- characters remain strongly recognizable in face, silhouette, outfit identity, and proportions;
- finish is richer and more cinematic than a TV-anime frame;
- high-value lighting, depth, atmosphere, detailed environments, bloom, particles, and composition;
- final goal is a premium light-novel illustration aesthetic.

Three asset levels:
1. Backgrounds
2. Character/environment compositions
3. Hero CGs

## Visual-change rule
Never change art just because several lines have passed.

Change visual state when a meaningful narrative change occurs:
- emotion;
- dramatic focus;
- character position;
- action;
- revelation;
- atmosphere;
- location/time;
- composition no longer represents the text.

## Action scenes
Action is presented as cinematic illustrated sequencing:
- hero CG;
- close-up;
- impact frame;
- camera motion;
- shake;
- flash;
- motion blur;
- particles;
- sound.

No playable combat or QTE.

## Audio
Initial scope:
- music;
- ambience;
- sound effects;
- no full voice acting.

Music changes at meaningful dramatic transitions, not per line.
Silence is valid direction.

## Return by Death
Consistent audiovisual identity:
- Subaru becomes central visual focus;
- scene stability/saturation/lighting changes;
- shadow-hand motif approaches him;
- ambience falls away;
- original project-owned sound treatment evokes the narrative function;
- blackout;
- checkpoint restoration.

Each death may vary details while preserving the recognizable signature.

## Static / Cinematic
### Static
Uses the same story and art, with scene/CG/expression transitions but without continuous decorative motion.

### Cinematic
Adds only safe, fluid layers:
- slow pan/zoom;
- parallax;
- blink;
- subtle breathing;
- hair/clothing secondary motion where supported;
- particles;
- rain/snow/smoke/fire/dust;
- lighting modulation;
- foreground depth movement.

Never deform an image merely to create motion.

## Production strategy
1. Engine and developer tooling
2. 30–45 minute vertical slice
3. Complete Volume 1
4. Later volumes only after the previous scope reaches final quality

The vertical slice must prove:
- main menu;
- language selection/switching;
- dialogue/thought/narration;
- scene changes;
- expression changes;
- dramatic-beat changes;
- backgrounds/compositions/hero CG;
- Static/Cinematic;
- history;
- save/load/autosave;
- chapters;
- Memories;
- audio;
- Return by Death;
- checkpoint restoration.

## Definition of done for a scene
- full intended text is present;
- PT/EN positions align through stable IDs;
- art still represents the current dramatic state;
- emotional changes receive appropriate visual response;
- music/ambience are correct;
- Static works;
- Cinematic works;
- save/load restores the correct scene state;
- history works;
- no broken references;
- reading remains comfortable;
- UI does not compete with the artwork.
