# T19 — Edge cases

1. **Empty workspace (admin baseline missing):** `/ws/` still renders the 2 balance buttons; the result panels show baseline values from the seed, no errors. Verified visually on both localhost (testsim) + Heroku (fresh testsim).
2. **After scenario edit (workspace dirty):** banner state preserved per T23; pressing Balance Solar successfully kicks off the BalanceJob path even though Goal Seek button is gone. Inferred from `test_bb_bal` passing.
3. **Direct call to old goal_seek endpoint:** the underlying `goal_seek` function is still callable internally (used by `apply-full-balance`); no public endpoint kept for it. A user POSTing to a hypothetical legacy URL would 404. Not a regression — the button no longer exists, so no caller path leads there.
