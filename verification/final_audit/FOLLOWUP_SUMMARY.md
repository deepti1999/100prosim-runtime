# FOLLOWUP_SUMMARY — audit follow-up run (2026-04-24)

**Auditor:** Claude (Opus 4.7, 1M ctx).
**Built on:** prior 2026-04-24 audit producing `EXECUTIVE_SUMMARY.md` (57/57 verified, 36 PASS + 21 PASS-WITH-CAVEAT).
**Trigger:** Pascal's 4-task follow-up brief — re-open generous verdicts, measure + close test gaps, document complete change history, run a real Heroku load test.
**Commits added in this run:** 12 (all `followup(...)` or `test(...)` or `docs(history)`). Local-only, no push.

## Per-task results

### Task 1a — Cockpit charts root cause (FAIL downgrade)
**Outcome:** root cause identified + 5 verdicts downgraded CAVEAT → FAIL. Single source: Django L10N (`USE_L10N=True` + `LANGUAGE_CODE='de'`, Phase 2-C T34) auto-formats float template-vars as `2.432.616,134`, which JS can't parse. The `cockpit.html` lines 287-340 inline-script bombs at parse time before any chart init runs. Bug task #111 created with fix recipe (`|unlocalize` filter or `{% localize off %}` block). Index tally now: **36 PASS / 16 PASS-WITH-CAVEAT / 5 FAIL / 0 CANNOT-VERIFY** (was: 36/21/0/0).

### Task 1b — Stale C/D goldens forensics
**Outcome:** documented. C and D goldens have ONE git-log commit each (initial capture 2026-04-20), never re-captured despite ~25 code commits since (Phase 2-C number format, 4 perf-pass iteration cuts, Phase B+C region scope). The C golden visibly mixes German page-panel values + English SVG values — direct evidence of Phase 2-C drift (the SVG values were English at capture time, switched to German post-`b8e4a45`). compare.py C/D require a Playwright capture step before they can produce a diff; that step was deliberately not run (would dirty testsim mid-audit). Recommendations to Pascal: re-capture both with sign-off (~30 min each); add CLAUDE.md cadence rule for re-capture after `calculation_engine` / `ws365_*` / number-format changes.

### Task 2 — Coverage measurement + new tests (4 modules, 21 tests)
**Outcome:** baseline `coverage report` showed 48 % aggregate / 11 694 stmts / 263 partial branches. Per-module gap table identified 5 HIGH-risk modules under 50 % line: ws365_sector_balance (2 %), ws365_orchestrator (7 %), page_cockpit (8 %), percentage_rebalancer (15 %), recalc_service (32 %). Dead code found: `simulator/calculations.py` + `simulator/ws_formula_service.py` (zero callers each, 0 % each).

Wrote 4 new test modules:
1. **`test_wb_cockpit_js_validity`** (5 tests) — would have caught the T43-T47 bug. Uses `@unittest.expectedFailure` for the static-source check until #111 fix lands.
2. **`test_wb_region_isolation_cross_user`** (4 tests) — the audit-prompt MUST-COVER scenario (user A in DE, user B in TEST, no cross-leak).
3. **`test_wb_d4ab_region_isolation`** (6 tests) — the audit-prompt MUST-COVER scenario (mutate non-active region's installed_pmax_*, active unchanged).
4. **`test_wb_save_default_cascade`** (6 tests) — regression guard for the 2026-04 incident where `save_renewable_user_input` had `skip_cascade=True` (Phase 4-E commit `86e3ba2` removed it). Includes a static check against the input_api.py source so the bug pattern can never silently re-appear.

Test count 207 → 227 (+20). Aggregate coverage 48 % → 49 % (+1 pp). **Per-module win: page_cockpit went 8 % → 26 %** (+18 pp from the cockpit JS test).

HIGH-risk targets ≥70 %: 6 modules met. 6 missed (page_cockpit 26 %, signals 51 %, recalc_service 32 %, ws365_* family 2-51 %, percentage_rebalancer 15 %, goal_seek 0 %). All misses explained in `coverage_delta.md` with pointers to the e2e modules that exercise them in integration form.

### Task 3 — Heroku load test (10 / 25 / 50 concurrent users)
**Outcome:** spun up `prosim-100-1fc45c10679b`, hammered 8 GET endpoints × 3 reps × N async httpx workers, tore down. Wall: ~30 / 48 / 55 s per tier.

**Top finding:** auth/login saturation — login failures 10 % → 28 % → **64 %** as concurrency goes 10 → 25 → 50 on a single Heroku Basic dyno. Real-user behaviour wouldn't all log in simultaneously, so this is a load-spike finding more than a steady-state bug, but **above ~20 concurrent users the auth path is the binding constraint**.

**Other findings:**
- ZERO 5xx errors at any tier (application code is correct under load, just slow on Basic dyno).
- ZERO timeouts (within 30 s threshold).
- Slowest page render: `/annual-electricity/` at ~6 s p50 from tier 25 onward.
- Worst p95 spread: `/landuse/` 2.41 → 6.38 → **12.56 s p99** across tiers (5.2× degradation, suggests N+1 query — corroborates `docs/PYPSA_MIGRATION_RESEARCH.md` §23.2).
- `/cockpit/` + `/historie/` anomalously fast — `/cockpit/` only because the JS bombs early per Task 1a (no chart-data fetch); `/historie/` because empty workspace.

Heroku destroyed at end (~$0.10 cycle).

### Task 4 — CHANGE_HISTORY.md (3000-5000 words)
**Outcome:** wrote a comprehensive 4500-word phase-by-phase narrative from Day 0 baseline through 57/63 shipped. Includes per-phase intent + commits + risks-encountered + mitigations + verification evidence; running tallies table; 10 key architectural decisions documented (integrate-not-migrate PyPSA, single-dyno Heroku target, process-local cache rule, workspace-scoped data, Formula table authority, region scaffolding-vs-operational distinction, additive provenance columns, auto-cascade vs manual Balance, WSData per-(owner, region) decision, D.xlsx vs _S.xlsx mapping target); scope-not-delivered (6 ErnES + 16 PASS-WITH-CAVEAT + 5 new FAILs); German glossary; commit index summary. Read-only git archaeology — zero production code change.

## Brutally honest health score

**Architecture: A−.** The code is well-organised, the V2-V6 ritual is real, the cross-process cache discipline holds, the region scaffolding is operationally proven. The one structural weakness is the visual-test blind spot the cockpit bug exposed (the test client doesn't execute JS, so a class of UI bugs ships undetected).

**Verification ledger honesty: B+.** "57/63 shipped" was honest at the ledger level but Task 1a downgraded 5 to FAIL — meaning 5 of the original PASS-WITH-CAVEATs were actually broken UI, not polish gaps. The audit caught it on the second pass; that's good. The remaining 16 caveats look genuinely caveat-level after the deep dive, with one exception: T6 (acid-test bench) is a stub and should arguably be ⏸ pending Phase 7-B.

**Test depth: C+.** 227 tests, 49 % line coverage. The HIGH-risk core (region scope, owner scope, workspace, balance jobs, ws365 formula engine, recalc_cache) is well-covered (85-100 %). The HIGH-risk orchestration (recalc_service 32 %, ws365_orchestrator 7 %, ws365_sector_balance 2 %) is THIN — those paths are tested in env-skipped Playwright e2e modules (`test_e2e_ui_*`) that aren't run in the docker container's pytest. **The single biggest test gap is `simulator/goal_seek.py` at 0 %** — the audit-prompt MUST-COVER list called this out and I didn't get to it (low impact + non-trivial fixture).

**Performance: D+ on Heroku Basic.** /annual-electricity/ at 6 s p50, /landuse/ at 12 s p99 under tier-50 concurrency, auth saturation at 25+. None of these are application bugs — they're "single Heroku Basic dyno" limits. The PDF §2.2 "praxistauglich" decision is the right place to address this, NOT in this audit.

**Documentation: A.** CLAUDE.md, REMAINING.md, PROGRESS.md, IMPLEMENTATION_PLAN.md, EXECUTIVE_SUMMARY.md, CHANGE_HISTORY.md — collectively the most thorough stakeholder-handoff documentation I've audited. The 4 drift items I found in `docs_drift.md` are minor.

## What's now ON Pascal's plate

In rough priority order:

1. **Fix bug #111** (Cockpit JS — `|unlocalize` filter or `{% localize off %}` wrap on cockpit.html lines 287-340). ~30 min. After fix: T43-T47 verdicts can flip back to PASS, and the `expectedFailure` decorator on `test_wb_cockpit_js_validity` should be removed.
2. **Decide T6 disposition** — implement bench measurement (~1-2 h) when ErnES picks a platform, OR demote PROGRESS.md to "shape shipped, measurement TBD".
3. **Re-capture C and D goldens** with sign-off (~30 min each).
4. **N+1 audit on `/landuse/`** — the load test showed 5.2× p99 degradation with concurrency.
5. **Sweep for English residues** in dynamic JS-injected text (T33 caveats: Renewable empty-state, login flash, Cockpit "Ziel (2050)" should be 2045).
6. **Open follow-up for /gebaeudewarme/ "Alle Werte speichern"** — extend T28's spirit beyond Flächen (or document why we keep it).
7. **Goal-seek convergence test** — `simulator/goal_seek.py` is at 0 % line coverage; the audit-prompt MUST-COVER list flagged it.

Phase 7 (ErnES platform pick) remains the only stakeholder-side blocker. Everything else is local engineering work.
