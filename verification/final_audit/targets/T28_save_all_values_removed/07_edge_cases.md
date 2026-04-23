# T28 — Edge cases

1. **Bookmark to old endpoint:** if a user had a bookmark to a Save-All endpoint, the underlying `/api/save-all-inputs/` still works. Not a regression.
2. **Mass-save still desired:** the per-row autosave (`autoSaveValue` debounce 1s) triggers on every change; users get implicit "save on edit". The "save all" semantic is now per-edit autosave + scenario snapshot.
3. **Scenarios → Save current Scenario:** verified visually via the top-bar `Szenarien` dropdown — present, functional. This is the canonical replacement per PDF.
