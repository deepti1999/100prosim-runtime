# Caveats accepted — index of non-breaking caveats retained post-audit

**Last updated:** 2026-04-24 (post-source-grounded-re-read — see `verification/final_audit/SOURCE_GROUNDED_ANSWERS.md`)

This document catalogues caveats identified in the 2026-04-24 final audit
(`verification/final_audit/index.md`) that Pascal has accepted as
**non-breaking** — evidence is sufficient, no fix is scheduled, and the
CAVEAT verdict is retained for provenance but not actionable work.

The initial 11 entries went through a source-grounded re-read; **3 of
them upgraded CAVEAT → PASS** (T10, T13, T31 — see
`SOURCE_GROUNDED_ANSWERS.md` Q2 + Q3) because the PDF literally
endorses the current behaviour rather than tolerating it.

The remaining 8 entries are **PDF-silent caveats** — the PDF does not
specify acceptance criteria for the rigor they describe. Evidence for
each is either (a) inspection + prior V5 verification rather than
re-run this audit, (b) a documented intentional scope reduction, or
(c) an observation logged without a gating threshold.

Each entry below links to the source 08_verdict.md (targets) or
cross_cutting doc — those files carry matching "Caveat accepted
2026-04-24" sections + source-grounded rationale quotes.

---

## Target verdicts (4)

*(T10, T13 both upgraded to PASS 2026-04-24 — see their 08_verdict.md.
Quotes from PDF §2.3.2 show the CLI path IS the PDF's proposal, not a
reduced interpretation.)*

### T18 — Shared admin baseline
**Caveat:** Two-user roundtrip not re-run in final audit pass
(would have dirtied testsim mid-audit).
**Rationale:** `AdminBaseline` singleton + V2 test
`test_bb_admin_baseline::test_baseline_shared_across_users` ✅ green;
prior V5 on `prosim-100-687a5505e19f` verified two-user flow.
→ `verification/final_audit/targets/T18_shared_baseline/08_verdict.md`

### T23 — Busy indicator + buttons functional after edit
**Caveat:** Live banner streaming not re-captured this audit
(would have needed ~90 s polling on a dirty workspace).
**Rationale:** `#balanceProgressBanner` DOM present per inspection;
prior V5 on `prosim-100-687a5505e19f` per VERIFICATION_STATUS.md §2
confirmed banner text updated every 2 s.
→ `verification/final_audit/targets/T23_busy_indicator_after_edit/08_verdict.md`

### T27 — Clear visual feedback on cascade
**Caveat:** Ephemeral per-save toast not re-captured this audit.
**Rationale:** Persistent "Letzte Änderungen" panel at page bottom
IS the durable feedback signal (visible in localhost/02_landuse.png
and 03_renewable.png); toast is a bonus layer, not load-bearing.
→ `verification/final_audit/targets/T27_visual_feedback_cascade/08_verdict.md`

*(T31 upgraded to PASS 2026-04-24 — see its 08_verdict.md. Quote from
PDF §2.4.3 shows the PDF itself proposes "WS Balance Wind / Solar" as
the post-consolidation button names.)*

### T62 — History snapshots-as-columns layout
**Caveat:** Populated layout not re-captured this audit
(would have dirtied testsim mid-audit).
**Rationale:** Empty-state visible in both localhost and Heroku
screenshots; prior V5 on `prosim-100-750ddc9416fd` per
VERIFICATION_STATUS.md Addendum confirmed Excel AH.Monitor column
layout renders correctly.
→ `verification/final_audit/targets/T62_history_columns_layout/08_verdict.md`

---

## Cross-cutting (4)

### cross_process_cache.md — Cross-process cache coherency
**Caveat:** Structural invariant verified by code inspection
(4 cache wipes still present at `run_balance_job` entry) rather than
fresh multi-dyno mutate→read test.
**Rationale:** Phase C synthetic TEST region verification from
2026-04-23 is itself a cross-process cache coherency proof;
`test_wb_balance_region_routing` ✅ green covers payload dispatch.
Fresh integration test worthwhile as next-major-change follow-up,
not as a blocker.
→ `verification/final_audit/cross_cutting/cross_process_cache.md`

### provenance_audit.md — Provenance spot check
**Caveat:** 2 of 10 random rows clicked-through this audit; the
other 8 not individually diffed against D.xlsx source.
**Rationale:** V2 test `test_wb_excel_provenance_import` 13/13 ✅
covers the import path (idempotent + assumption_text + source_url +
orphan_csv + origin field); diversity-of-rows sweep is nice-to-have,
not load-bearing.
→ `verification/final_audit/cross_cutting/provenance_audit.md`

### heroku_cold_boot.md — Heroku cold boot timings
**Caveat:** Single-sample observational timings, no gating threshold.
**Rationale:** PDF §2.2 uses *"praxistauglich"* (practically usable)
with no numeric target. Observed timings logged for baseline;
architectural follow-ups (Verbrauch N+1, Bilanz daily-series, Cockpit
chart-data) documented in `PYPSA_MIGRATION_RESEARCH.md` §23.2 but not
gated on cold-boot audit.
→ `verification/final_audit/cross_cutting/heroku_cold_boot.md`

### security_sweep.md — Security sweep
**Caveat:** Auth/CSRF/owner-scope wired per code inspection + V2
tests; no active penetration testing (brute-force, SQL injection, XSS,
session fixation).
**Rationale:** Django auto-hardening + V2 coverage sufficient for the
current audit; pen-testing explicitly out of scope per audit charter.
No identified vulnerabilities.
→ `verification/final_audit/cross_cutting/security_sweep.md`

---

## Escalation policy

If a caveat above escalates to blocking behaviour (e.g. two-user
shared baseline actually breaks, live banner stops updating, a
production security incident), upgrade it from "accepted" to
"open" in `index.md`, open a task with T-ID, and follow the
V2-V6 ritual per CLAUDE.md §"Per-item verification".

This document is an **acceptance ledger**, not a TODO list.
