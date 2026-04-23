# Final audit — 57 shipped stakeholder targets

**Run started:** 2026-04-24
**Auditor:** Claude (Opus 4.7, 1M ctx) under Pascal's autonomous-run instruction.
**Source of truth:** `verification/final_audit/pdf_text/portierung_bestandsaufnahme.txt` (extracted from `docs/stakeholder/260403_Portierung_Bestandsaufnahme.pdf` via pdftotext -layout) + companion DE/EN markdown extracts in `docs/stakeholder/`.
**Scope:** Every stakeholder target shipped per `PROGRESS.md` and `REMAINING.md` — 57 of 63 (T6, T8–T63 minus T1–T5 + T7 which are external-gated on ErnES).

## Methodology — what verification means here

Per CLAUDE.md V2–V6 ritual + the user's audit prompt, each shipped target should have:

| Layer | What I do |
|---|---|
| **Stakeholder ask** | Quote from PDF page (verified against extracted text), German + English. |
| **Implementation** | Commit list, files, LOC delta, test module. |
| **Tests (V2)** | Run the relevant test module(s); record pass/fail per assertion. Stale tests: update against current behaviour and commit. Missing tests for behaviour-changing target: write one. |
| **Localhost (V4)** | Real `browser_navigate` + `browser_take_screenshot` + `browser_console_messages`. NOT `fetch()` inside `browser_evaluate`. |
| **Heroku (V5)** | Same against the live URL. Single Heroku spin-up shared across the whole audit; reset testsim workspace between dirty tests. |
| **Performance** | First-hit timings via network/HAR + `performance.now()` for any interactive control. Document, don't gate. |
| **Edge cases** | 3 minimum: empty state, invalid input, concurrent user where applicable. |
| **Verdict** | `PASS`, `PASS-WITH-CAVEAT`, `FAIL`, or `CANNOT-VERIFY-LOCALLY`. |

## Constraints (per audit prompt + CLAUDE.md)

- **Read-only on production code.** `git diff main~0` for the audit branch must show only `verification/`, possibly test file updates, possibly doc corrections. Zero behaviour change to `simulator/`, `calculation_engine/`, `seed/`.
- **Goldens never auto-update.** If `compare.py` exits 1, investigate; record the deltas; do NOT re-capture without explicit Pascal sign-off.
- **Bugs found ≠ fix.** This is an audit run; record in 08_verdict.md as PASS-WITH-CAVEAT or FAIL, do not fix.
- **Heroku: ONE spin-up, ONE teardown.** Cycling per target would burn ~$5+. Workspace reset via the CLAUDE.md snippet between dirty tests.
- **Visual = eyeballed screenshot, not regex over `fetch()` HTML.**
- **PDF wins over .md extracts.** Cross-check claims against the extracted PDF text.
- **Commits local-only.** `verify(T<nn>): <verdict> — <summary>` per target; `verify(cross-cutting-<name>): <summary>` for cross-cutting docs.

## Honest limitations of this run

- **Time bound.** A single Claude session cannot produce 8 high-quality docs × 57 targets in one go. I commit after every batch so partial work survives. Targets verified with abridged evidence note the abridgement explicitly.
- **Mid-run format pivot.** T6, T19, T20, T28 use the full 8-file structure (`01_stakeholder_ask.md` … `08_verdict.md`). For the remaining 53 targets I compress to **two** files per target:
  - `01_stakeholder_ask.md` — PDF quote + acceptance.
  - `08_verdict.md` — combined evidence (sections 02-07 inline) + verdict.
  This change preserves the V2-V6 evidence ladder per target but avoids the 456-file blowup. The 8-file targets stay as-is for reference.
- **PDF extraction.** `pdftotext -layout` mangles some umlauts in the German source (e.g. "Funk�onalit�t" instead of "Funktionalität"). The extracted text is structurally correct and section-numbered; for canonical wording I cross-reference `260403_Bestandsaufnahme_DE.md` and `260403_Bestandsaufnahme_EN.md` translations.
- **Performance numbers are observational, not gated.** Heroku basic dyno timings vary ±2× call-to-call; a single sample is not a percentile. Numbers documented with sample-size caveats.
- **Two-user concurrency edges** are sketched (one browser tab + one curl/heroku-shell session), not run as N-user load tests.

## Layout

```
verification/final_audit/
├── README.md                          (this file)
├── pdf_text/
│   └── portierung_bestandsaufnahme.txt  (canonical PDF extract)
├── targets/
│   └── T<nn>_<slug>/
│       ├── 01_stakeholder_ask.md
│       ├── 02_implementation.md
│       ├── 03_tests.md
│       ├── 04_localhost_evidence.md
│       ├── 05_heroku_evidence.md
│       ├── 06_performance.md
│       ├── 07_edge_cases.md
│       ├── 08_verdict.md
│       └── screenshots/
│           ├── localhost/
│           └── heroku/
├── cross_cutting/
│   ├── pdf_coverage.md
│   ├── regression_A.md / regression_C.md / regression_D.md
│   ├── test_suite_full.md (+ .log)
│   ├── e2e_ui_full.md
│   ├── cross_process_cache.md
│   ├── region_round_trip.md
│   ├── provenance_audit.md
│   ├── heroku_cold_boot.md
│   ├── security_sweep.md
│   └── docs_drift.md
├── index.md                           (running verdict table)
├── EXECUTIVE_SUMMARY.md
├── heroku_up.log
└── heroku_down.log
```

## Per-target verdict legend

| Verdict | Meaning |
|---|---|
| `PASS` | All evidence layers green; PDF ask satisfied without caveat. |
| `PASS-WITH-CAVEAT` | Functionally complete; non-blocking gap, abridged evidence, or known minor mismatch documented. |
| `FAIL` | A required guarantee is broken; new task created. |
| `CANNOT-VERIFY-LOCALLY` | Audit cannot reach the artefact (e.g. external-gated, file not in bundle, Heroku mid-spin-up). |
