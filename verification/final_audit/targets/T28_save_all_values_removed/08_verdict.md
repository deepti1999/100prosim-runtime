# T28 — Verdict: **PASS-WITH-CAVEAT**

PASS at the literal level: "Save All Values" button is absent from `/landuse/` on both localhost and live Heroku. PDF §2.4.5 ask satisfied for the page the PDF named.

**Caveat:** the same UX pattern (a per-page "save all" button that PDF called "redundant + confusing") still exists on `/gebaeudewarme/` as **"Alle Werte speichern"**. This is consistent with the literal target scope (T28's text in `IMPLEMENTATION_PLAN.md` §3 says "Remove 'Save All Values' button from Flächen page"), but the spirit of the §2.4.5 complaint extends beyond just the Flächen page.

**Recommended follow-up (NOT done in this audit):** consider whether to apply the same removal to /gebaeudewarme/ (and any other parameter page that has a similar mass-save button), or whether Gebäudewärme's button has unique semantics worth preserving. Open as a future task; outside the literal T28 scope.
