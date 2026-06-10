# SHIP-READY SUMMARY — 4-task fix bundle (2026-04-24)

**Author:** Claude (Opus 4.7, 1M ctx) under Pascal's autonomous fix-task brief.

## Before / after verdict tally

| State | PASS | PASS-WITH-CAVEAT | FAIL | Total |
|---|---:|---:|---:|---:|
| Original audit (2026-04-24) | 36 | 21 | 0 | 57 / 57 |
| Follow-up audit (Task 1a downgrade) | 36 | 16 | **5** | 57 / 57 |
| **This fix-bundle (post)** | **42** | **15** | **0** | 57 / 57 |

Net: +6 PASS, −1 CAVEAT, −5 FAIL. **No FAILs remain on any shipped stakeholder target.**

## Commits landed (6 total, in order)

| # | Sha | Subject |
|---:|---|---|
| 1 | `f86aae9` | fix(cockpit): T43-T47 de-locale numeric output so JS parses (#111) |
| 2 | `a026fd0` | docs: update verdict ledger post-#111 fix — T43-T47 FAIL → PASS |
| 3 | `7c6cfd5` | regression: re-capture C+D post Phase-2C drift — Pascal approved |
| 4 | `0392dc8` | test(goal-seek): cover convergence + edge cases — closes 0% gap |
| 5 | `d7822c3` | feat(T6): real acid-test bench script with A/C/D scenarios — closes stub (T6) |
| 6 | `2e5f068` | docs: update verdict ledger post-T6 — bench harness real (T6) |

## What changed per task

**Task 1 — bug #111 (cockpit JS bombs):** `cockpit.html` now renders 36 chart values into a hidden `<div id="bilanzDataPayload">` with `|unlocalize`-d `data-*` attributes; JS reads via `dataset` + `parseFloat()`. Visible page DOM keeps German formatting. V4+V5 verified: all 3 charts attach, delta table populates with 4 sector rows. T43-T47 restored FAIL → PASS.

**Task 2 — C/D goldens:** `regression/capture_C.py` (HTTP-driven via `/api/ws/summary/` + scrapes inline `vals` JS object) and `regression/capture_D.py` (verbrauch edits + multi-pass recalc + solar variant) emit raw unlocalized floats. New goldens replace stale Phase-2C-drifted ones. `compare.py C` and `compare.py D` both exit 0.

**Task 3 — goal_seek coverage:** `simulator/test_wb_goal_seek.py` (22 tests over the 3 solvers) lifts `goal_seek.py` from 0% → **100%** line coverage. Closes audit-prompt MUST-COVER item.

**Task 4 — T6 bench:** `scripts/bench_acid_test.py` replaces the always-`null` stub with real `time.perf_counter()` measurement. V4 medians on local stack: A=0.91s, C=0.82s, D=4.14s. T6 upgraded CAVEAT → PASS.

## Ship-readiness

**Project is ship-ready.** Zero FAIL verdicts. 42 PASS / 15 PASS-WITH-CAVEAT covers every shipped stakeholder target with at least one form of V4 + V5 evidence. Test suite 251/251 green (was 207 before audit-and-fix work; +44 tests). Phase 7 (ErnES platform pick) remains the only stakeholder-side blocker for T1-T5+T7.
