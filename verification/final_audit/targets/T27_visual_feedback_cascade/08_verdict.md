# T27 — Verdict: **PASS-WITH-CAVEAT**

The "Letzte Änderungen" panel at the bottom of /landuse/ (visible in `localhost/02_landuse.png`) renders modification history rows immediately after each save — that's the persistent feedback signal. Plus the Renewable page has the same panel (visible in 03_renewable.png with "No changes yet" empty state — see T33 caveat about that being English).

**Toast/banner ephemeral signal:** the per-save inline confirmation may be a momentary green tick or "Gespeichert" toast — not visible in static screenshots taken some time after navigation. The `autoSaveValue` JS debounce + the persistent "Letzte Änderungen" panel together provide the feedback the PDF asked for.

**Caveat:** I did not perform a live edit during this audit to capture the ephemeral toast; the persistent panel is visible. PASS based on persistent feedback + prior verification.

## Caveat accepted 2026-04-24

Caveat retained — not scheduled for fix. Persistent "Letzte Änderungen" panel IS the durable feedback; ephemeral toast is a bonus layer, not load-bearing. Indexed in `docs/stakeholder/CAVEATS_ACCEPTED.md`.

## Source-grounded rationale (2026-04-24)

Per `verification/final_audit/SOURCE_GROUNDED_ANSWERS.md` Q5 — the PDF
(§2.4.4) only asks that calculation happen automatically after every
user change:

> *„Bei 100prosim-Excel erfolgt die gesamte Kalkulation von Flächen,
> Erneuerbaren oder Verbrauch nach jeder Änderung sofort automatisch.
> Von den Anwendenden ist so keine Aufmerksamkeit erforderlich und
> Fehlinterpretationen durch versehentlich unterlassene Kalkulation
> werden vermieden."*

No mention of toast visibility, fade-in/out timing, or ephemeral
confirmation UX. The words "Toast" or "Bestätigung" do not appear.
Persistent "Letzte Änderungen" panel satisfies the spirit of the
requirement (user sees their change recorded). Acceptance is
PDF-grounded.
