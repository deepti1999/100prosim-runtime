# T25 — Verdict: **PASS**

`save_renewable_user_input` previously had `skip_cascade=True` which was the bug — Phase 4-E commit `86e3ba2` removed that flag. Now Renewable saves trigger the same cascade as Verbrauch saves. `test_bb_renewable_edit` ✅ green. CLAUDE.md "save() vs save(skip_cascade=True)" entry documents this fix specifically.
