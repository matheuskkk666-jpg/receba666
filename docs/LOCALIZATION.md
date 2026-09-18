# Localization

## Model
Portuguese and English are parallel first-class editions.

A shared stable narrative ID identifies the same story position across editions.

Example:

```text
arc01.ch01.sc003.0042
```

Switching language must:
- preserve this ID;
- preserve current scene;
- preserve visual state;
- preserve unlocked state;
- change only localized content and language-sensitive UI/assets where applicable.

## Terminology
Do not normalize terminology across editions merely for consistency.
If the Portuguese and English editions make different established choices, preserve those choices unless the user explicitly requests editorial normalization.

## Source handling
Narrative text may be imported only from material the user is authorized to provide/use.

For each localized entry, keep editorial provenance/status metadata outside the player-facing UI where practical.

Suggested statuses:
- imported_reviewed
- imported_unreviewed
- generated_needs_review
- manually_revised

If a passage is unavailable in one selected edition but available in another authorized source, a missing edition may be translated and marked `generated_needs_review`.

## Alignment
Alignment is by narrative meaning/position, not by identical paragraph wrapping.

If one edition genuinely requires different segmentation, support grouped/linked units rather than dropping text.

## UI localization
All UI labels, menus, chapter navigation, settings, Memories labels, and player-facing system messages must be localizable.

Do not hard-code Portuguese strings into core screens.

## Testing
For every localized screen/feature:
- test Portuguese;
- test English;
- test runtime language switching;
- test long-string overflow;
- test save/load across a language change.
