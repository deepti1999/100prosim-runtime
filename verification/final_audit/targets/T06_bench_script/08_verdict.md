# T6 — Verdict: **PASS-WITH-CAVEAT**

## Headline

The harness's **shape** is shipped (file exists, calling pattern, env vars, log format, JSON object schema, header bootstrap). The harness's **measurement** is NOT shipped — it is a stub that always emits `elapsed_seconds: null` with `status: "stub"` and a `"harness not yet implemented; Phase 7-B"` note.

`PROGRESS.md` and `REMAINING.md` mark T6 as ✅ Shipped, but per `IMPLEMENTATION_PLAN.md` §5 0-C the explicit deliverable text is:

> *"Creates clean workspace state, applies the two changes, triggers Balance Solar, times end-to-end."*

That is not what the script does today.

## Why PASS-WITH-CAVEAT and not FAIL

1. The PDF deliverable is a **measurement instrument**, not a result. The instrument's interface (CLI invocation + JSON output + log file) is locked in and a future Phase 7-B implementation can drop in measurement without changing the calling contract.
2. T5 ("run the acid test") + T7 ("if it fails, trigger architecture review") are both `⏸ Waiting on ErnES` per `REMAINING.md`. There is no platform to actually benchmark against in a meaningful way today (Heroku Basic is a known-slow placeholder).
3. The script's TODO is honest and explicit — it does not pretend to measure.

## Why this is still a real gap

The PDF text "Dieser Test wird damit zur Nagelprobe" makes the acid-test the deciding question for production-readiness. Without an end-to-end timed harness, even a well-set-up ErnES platform cannot be measured against the 5.8 s Excel baseline objectively. When Phase 7-B opens, the FIRST work is finishing the harness body.

## Recommended next action

Open a follow-up task in this run's deliverables: when Phase 7-B is unblocked, replace the stub with a real Playwright (or `requests`-based) flow:
1. Authenticate via session login.
2. POST `/api/testsim-reset/` (or use the CLAUDE.md `testsim` reset snippet via heroku run shell).
3. Edit `LU_6` user_percent = 2.3.
4. Edit `9.3.4` user_value = 60 (in GW; check current units).
5. Trigger `/api/ws/apply-full-balance/` with `t0 = perf_counter()`.
6. Poll the resulting `/api/ws/balance-job/<id>/` until `status == 'succeeded'`.
7. `elapsed = perf_counter() - t0`.
8. Append the populated JSON line.

Estimated effort: 1–2 hours. Cannot run before Phase 7-B because it needs to be measured ON the ErnES platform, not on Heroku Basic (which is the known-bad placeholder, not the test target).

## Audit checklist

- [x] Script exists at `scripts/bench_acid_test.sh`.
- [x] Reads `BASE_URL` env var.
- [x] Captures `commit_sha`.
- [x] Appends JSON line to `docs/stakeholder/BENCHMARK_LOG.md`.
- [x] Bootstraps log file on first run.
- [ ] Actually measures Balance Solar elapsed time. (← stub)
- [ ] Real cycle-over-cycle data in `BENCHMARK_LOG.md`. (← only the stub line is there)

## New audit task

`tasks/audit-T6-followup.md` (this run's "tasks discovered" list) — implement real measurement loop in `scripts/bench_acid_test.sh` when Phase 7-B opens. NOT a fix, NOT done in this audit.
