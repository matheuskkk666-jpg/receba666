# Narrative & Content Pipeline

## Purpose
Scale to long-form light-novel content without dense metadata for every line.

## Pipeline
```text
authorized source text
    ->
segment into narrative units
    ->
assign stable IDs
    ->
align PT/EN
    ->
group into scenes
    ->
identify dramatic beats
    ->
add sparse direction overrides
    ->
resolve/create assets
    ->
validate
    ->
preview
    ->
human review
    ->
integrate
```

## Scene authoring
A scene defines defaults once.

```yaml
scene: capital_market_01
defaults:
  background: capital_market_sunset
  music: market_gentle
  ambience: capital_evening
  lighting: sunset_warm
  shot: medium
  animation: subtle

sequence:
  - dialogue: arc01.ch01.sc003.0042
  - dialogue: arc01.ch01.sc003.0043

  - expression:
      emilia: concerned

  - dialogue: arc01.ch01.sc003.0044

  - beat: tension_rising

  - dialogue: arc01.ch01.sc003.0045
```

Do not repeat unchanged state.

## Dramatic beats
Reusable direction presets may include:
- tension_rising;
- relief;
- dread;
- introspection;
- discovery;
- action_burst;
- silence_after_shock.

Beats adjust presentation. They must not invent story facts.

## Asset decision ladder
When the current visual no longer fits:
1. expression change;
2. pose/focus change;
3. camera/shot change;
4. new composition;
5. Hero CG.

## Production gate
Do not bulk-ingest story content until:
- data format is stable;
- validator exists;
- developer preview exists;
- runtime language switching is proven;
- save/load state restoration is proven;
- Static/Cinematic share the same scene definition.

## Placeholder content
Until authorized story content is supplied, use original placeholder scenes.

## Editorial review
Automated analysis may suggest dramatic beats, but checked-in scene data is the source of truth.
