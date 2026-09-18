# Architecture

## Goals
- Data-driven narrative and direction.
- Sparse scene metadata.
- Stable IDs.
- Easy preview and validation.
- Static/Cinematic share one content definition.
- PT/EN share one narrative position model.

## Recommended layout

```text
game/
  core/
    scene_director/
    progression/
    persistence/
    localization/
    animation/
    audio/
  narrative/
    arc_01/
      chapter_01/
  translations/
    pt_BR/
    en/
  scenes/
    arc_01/
  assets/
    backgrounds/
    characters/
    compositions/
    cg/
    overlays/
    particles/
  audio/
    music/
    ambience/
    sfx/
  ui/
    main_menu/
    reading/
    pause/
    history/
    chapters/
    memories/
    settings/
  dev/
    preview/
    validation/
tests/
tools/
docs/
```

Exact file extensions and Ren'Py module boundaries may evolve, but separation of responsibilities should remain.

## Stable narrative position
Use IDs such as:

```text
arc01.ch01.sc003.0042
```

The ID identifies narrative position, not language.

Never derive identity from file line number.

## Scene state model
A scene starts with defaults:

```yaml
scene: capital_market_01
defaults:
  background: capital_market_sunset
  music: market_gentle
  ambience: capital_evening
  lighting: sunset_warm
  shot: medium
  animation: subtle
```

Sequence entries inherit previous state.

Most entries should be light:

```yaml
- dialogue: arc01.ch01.sc003.0042
- dialogue: arc01.ch01.sc003.0043
```

Only changes are declared:

```yaml
- expression:
    emilia: concerned

- beat: tension_rising

- shot: close_subaru
```

## Dramatic beats
Dramatic beats are reusable direction presets, not automatic storytelling AI.
They may modify camera, animation intensity, music gain, background blur, lighting tone, or ambience.

Example:

```yaml
beat: tension_rising
```

Do not let a beat force character expressions unless explicitly designed for that specific character/situation.

## Scene Director responsibilities
- load scene defaults;
- apply sparse state overrides;
- resolve active visual state;
- resolve current narrative ID;
- display the selected language string;
- switch language without moving position;
- restore deterministic state after load;
- expose active state to history/preview/debug tools;
- respect Static/Cinematic presentation policy.

## Localization model
Keep narrative identity separate from localized strings.

Conceptually:

```yaml
id: arc01.ch01.sc003.0042
pt:
  speaker: Subaru
  text: "..."
en:
  speaker: Subaru
  text: "..."
```

Implementation may use separate files per language if cleaner. The invariant is shared ID alignment.

## Persistence
Persistent progression:
- furthest narrative position;
- reached chapters;
- seen CGs;
- seen scenes;
- encountered characters;
- revealed character facts;
- experienced death memories;
- preferred language;
- presentation mode;
- settings.

Save-state persistence:
- current narrative ID;
- complete resolved scene state needed for deterministic restoration;
- current scene/chapter;
- relevant transient presentation state.

## Validation
Create an offline validator that fails on:
- duplicate narrative ID;
- missing required localized entry;
- invalid scene reference;
- missing asset/audio reference;
- invalid character/expression;
- invalid dramatic beat;
- unlock entry with no condition;
- unreachable referenced scene;
- malformed chapter metadata.

Warnings may be used for editorial issues, but broken references should fail validation.

## Developer preview
Provide a development-only screen/command to launch directly into:
- scene;
- narrative ID;
- language;
- Static/Cinematic mode.

Provide shortcuts to:
- next/previous dramatic beat;
- reload scene data where practical;
- inspect resolved scene state.

## First implementation constraint
Do not ingest large amounts of real story content while core systems are unstable.
Use original placeholder prose for the vertical slice until the content pipeline is proven.
