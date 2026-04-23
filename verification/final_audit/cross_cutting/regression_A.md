# Cross-cutting — regression scenario A

**Scenario:** `A-baseline-readonly` — login + visit every main page + capture top-line numbers (97 fields).
**Run:** 2026-04-24 against the docker-compose stack.
**Command:** `docker compose exec -T web python regression/compare.py A-baseline-readonly`

## Result

```
OK A-baseline-readonly: current matches golden (97 fields)
exit 0
```

**PASS — 97/97 fields match the committed golden** (`regression/golden/A-baseline-readonly.json`, captured 2026-04-22 with Pascal's sign-off per `REGRESSION_DIFF_REPORT.md`).

## What this proves

Scenario A is the broadest read-only check we have:
- All main pages render successfully on a fresh seed.
- Top-line numbers (LandUse hectares, Renewable status/ziel values, Verbrauch totals, Bilanz summary) are byte-identical to the captured golden.
- No drift from Phase A/B/C §2.3 work, no drift from Phase 5 chart rework, no drift from any iteration cuts.

## Did NOT run

- **Scenario C** (WS Balance) — would dirty the workspace and require ~90s polling. Skipped to keep the audit deterministic; per `VERIFICATION_STATUS.md` §"Scenarios C and D" the goldens are pre-Phase-2 and would exit 1 on translation drift, requiring deliberate re-capture with Pascal sign-off (NOT done in this audit).
- **Scenario D** (full flow) — same reason.

## Verdict
**PASS for A.** C/D not re-run; their goldens remain stale-by-design pending Pascal-approved re-capture.
