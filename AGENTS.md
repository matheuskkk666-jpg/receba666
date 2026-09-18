# AGENTS.md

## Mission
Build a cinematic, linear light-novel experience in Ren'Py. The project is not an RPG and must never drift into one.

## Non-negotiable product rules
1. Do not add narrative choices, combat, exploration, QTEs, stats, inventories, achievements, or progression mechanics unless explicitly requested.
2. Do not summarize, rewrite, omit, or "improve" narrative text. Narrative content must come from material the user is authorized to provide/use.
3. Do not place a permanent bottom action bar over the artwork.
4. During reading, the only permanent control may be a small icon-only hide-UI button in the upper-right.
5. ESC opens the pause menu over a dimmed/blurred version of the current scene.
6. Design target is 1920x1080, 16:9.
7. Portuguese and English are independent editions tied to shared stable narrative IDs.
8. Changing language during reading must keep the exact narrative position and scene state.
9. Do not create a new illustration because an arbitrary number of lines passed. Visual changes must follow dramatic changes.
10. Static and Cinematic modes must use the same content and scene definitions.
11. If animation harms the artwork, keep the artwork static.
12. Do not reveal future chapter titles, characters, CGs, deaths, locations, or facts in secondary menus.

## Architecture rules
- Keep narrative content, presentation, UI, assets, persistence, localization, audio, and developer tools separated.
- Avoid a monolithic script.rpy.
- Scene direction is stateful: scene defaults + sparse overrides + reusable dramatic-beat presets.
- Most narrative entries should contain only a text ID/speaker reference.
- Stable narrative IDs must never depend on physical file line numbers.
- Prefer data-driven systems over bespoke code per scene.
- Reuse Ren'Py capabilities where appropriate instead of rebuilding save/load, rollback, screens, ATL/transforms, and persistence from scratch.

## Quality rules
A task is not complete because code parses or launches.

For every meaningful feature:
- run the relevant automated validation;
- launch the project when runtime behavior is affected;
- test 1920x1080;
- test mouse and keyboard paths where applicable;
- test Portuguese and English when text/UI is affected;
- verify save/load state when persistence is affected;
- verify Static and Cinematic modes when scene presentation is affected.

If a task cannot be fully tested in the current environment, say exactly what was tested and what remains unverified.

## Workflow
- Do not work directly on main after repository bootstrap.
- Use focused branches and pull requests.
- Keep PRs scoped to one subsystem or milestone.
- Explain architectural deviations in the PR description.
- Do not begin bulk Volume 1 content ingestion before the vertical slice architecture is accepted.

## Copyright / content handling
- Do not fetch or reproduce copyrighted light-novel text that the user has not supplied or authorized.
- Placeholder narrative must be original.
- Do not copy protected anime audio, music, or images into the repository.
- When testing Return by Death, use original placeholder effects and audio assets.
