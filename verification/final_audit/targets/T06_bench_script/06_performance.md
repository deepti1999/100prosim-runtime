# T6 — Performance

## What this target promises

T6 is the **measurement instrument**, not a perf-optimisation. It is supposed to *let us measure* whether the architecture meets "praxistauglich" response times on the chosen ErnES platform.

## Performance the instrument *would* report

If implemented, the script would measure end-to-end Balance-Solar elapsed time for the §2.2 acid test (onshore 2.0→2.3 %, offshore 70→60 GW). PDF baseline numbers:
- Excel: 5.8 s
- 100prosim-Web on Deepti's hosting (2026-04-03): 120 s
- 100prosim-Web on current Heroku Basic (2026-04-21 perf-pass cut): ~120 s → ~5–6 min for full convergence; the iteration-count cuts brought unbalanced cases from ~5 min to ~2 min.

## Performance the instrument *currently* reports

`null`. See `02_implementation.md` and `03_tests.md`.

## What this means for the audit

Because T6's job is to enable benchmark — not to be benchmarked itself — there is no "p50/p95 for T6". The harness runs in <1 s today (it just appends a stub line).
