# Final closure — 2026-04-24

**Status: project objectively closed pending ErnES Phase 7 handover.**

## Target verdict tally (57 shipped)

| Verdict | Count |
|---|---:|
| **PASS** | **53** |
| PASS-WITH-CAVEAT (ACCEPTED — PDF-silent rigor) | 4 |
| OPEN | 0 |
| FAIL | 0 |

Plus 4 cross-cutting ACCEPTED with PDF-silence rationale, 3 CANNOT-VERIFY
(env-gated — regression C/D golden re-capture gated on Pascal; e2e-ui
requires local Postgres), 4 clean PASS. Six targets (T1-T5, T7) remain
external-gated on ErnES choosing a compute platform — expected.

## What landed this session (11 commits, 0 backend regressions)

- **Fix 1** — T33 German-UI residues (3 primary + 7 sibling strings).
- **Fix 2** — T28 "Save All Values" scope aligned to PDF §2.4.5 literal
  (Flächen-only); /gebaeudewarme/ retained intentionally.
- **Fix 3** — 4 docs-drift items in CLAUDE.md + docs_drift.md.
- **Fix 4** — T54 Gasspeicher 83 vs 87 investigation (Excel authoritative).
- **Fix 5** — 11 caveats initially accepted as non-breaking.
- **Research pass** — Q1–Q10 grounded in PDF verbatim + Excel openpyxl.
- **Action 1** — T10, T13, T31 ACCEPTED → PASS on source-grounded reading.
- **Action 2** — T54 math fix shipped (signals.py:175 → gas_storage basis);
  all three Gasspeicher Tages now 87 (was 83/87/87); goldens C + D
  re-captured; HARDCODED_VALUES_TRACE §6 corrected.
- **Action 3** — 7 remaining ACCEPTED caveats annotated with PDF-silence
  rationale (verbatim quotes or demonstrated absence); Findings A + B
  deferred to REMAINING.md §4.

## Every ACCEPTED caveat is now PDF-grounded

- T18, T23, T27, T62 — PDF silent on specific rigor criterion.
- cross_process_cache, heroku_cold_boot, security_sweep — PDF silent.
- provenance_audit — V2 covers import; 10-row diversity sweep polish.

## Deferred spot-check findings (REMAINING.md §4)

- **Finding A** — Renewable 9.1.2 net-vs-gross scoping (popover clarifier, ~15 min).
- **Finding B** — GebaeudewaermeData 2.0/2.3/2.6/2.10 display 1000× scale
  (seed fix, ~30 min + Heroku cycle).

Both non-blocking; neither affects Bilanz / WS365 / any calculation.

## Next action

ErnES picks a compute platform → Phase 7 acid test (T5/T7) → handover.
Stakeholder-side; nothing for us to do here.

Full thesis suite: **263/263 green**. Heroku: destroyed. Repo: clean.
