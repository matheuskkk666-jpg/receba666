# Quality Bar

## Principle
"Runs" is not the same as "finished."

A feature is accepted only when the player-facing flow works and remains consistent with the GDD.

## Mandatory checks for every PR

### General
- project launches;
- no obvious Ren'Py errors;
- no broken asset references;
- validator passes;
- no new monolithic subsystem;
- documentation updated when architecture changes.

### 1920x1080 UI
- no clipping;
- no overlap;
- no unreadable text;
- no accidental permanent bottom HUD;
- keyboard and mouse navigation work;
- ESC behavior is correct.

### Localization
When affected:
- PT-BR works;
- EN works;
- runtime language switch works;
- long strings do not break layout;
- save/load after switching language preserves position.

### Scene system
When affected:
- sparse state inheritance works;
- expression changes do not reset unrelated scene state;
- dramatic beats change only intended state;
- loading restores deterministic state;
- Static/Cinematic consume the same scene definition.

### Save/progression
When affected:
- Continue returns to the correct narrative position;
- chapter unlock state persists;
- future chapter titles remain hidden;
- Memories reveal only seen content;
- history inspection does not silently overwrite progress.

## Vertical slice acceptance
One continuous 30–45 minute placeholder journey must demonstrate:
- new game and continue;
- PT/EN and runtime language switch;
- dialogue, thought, and narration;
- chapter card;
- multiple locations;
- expression and dramatic-tone changes;
- composition change and Hero CG;
- Static and Cinematic modes;
- music, ambience, and SFX;
- history;
- manual save/load and autosave;
- chapter navigation;
- Memories;
- one death sequence;
- Return by Death presentation;
- checkpoint restoration.

## Visual standard
After each scene ask:
"Does this feel like a more beautiful way to experience the light-novel passage?"

If animation distracts, reduce it.
If UI distracts, simplify it.
If art no longer matches the emotional state, revise direction.
If a feature exists only because games usually have it, remove it.
