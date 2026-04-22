# 100ProSim documentation

Three reference documents. Read in this order if you're inheriting the project.

## [PERFORMANCE.md](PERFORMANCE.md)

**Read first.** What changed during the 2026-04-21 perf pass, why, what the measured impact was, how the caches compose, and how to revert safely. Covers:

- The original problem (balance 3-10 min on Heroku)
- Each optimization that shipped (7 perf steps + 3 iteration cuts + early-exit gates)
- Steps investigated and skipped, with evidence
- Shadow-parity safety gates (one of which caught real bugs pre-ship)
- Cache invalidation strategy
- File inventory
- What's still on the roadmap (not urgent)

## [HEROKU.md](HEROKU.md)

Deployment guide for the live app at `prosim-100.herokuapp.com`. Covers:

- Provisioned resources + monthly cost (~$20/mo)
- Required env vars
- Routine operations (deploy, seed, create test user, check status, tail logs)
- Smoke test steps
- Recovery procedures (regression, testsim drift, build failure, rollback)
- Scaling paths

## [PYPSA_MIGRATION_RESEARCH.md](PYPSA_MIGRATION_RESEARCH.md)

Earlier research on selective PyPSA integration. Not adopted (see §23 for the final decision). Kept as reference for a future engineer who wants to revisit long-duration storage optimization.

## [stakeholder/](stakeholder/)

ErnES stakeholder input and the action items derived from it.

- [`260403_Portierung_Bestandsaufnahme.pdf`](stakeholder/260403_Portierung_Bestandsaufnahme.pdf) — original German stocktaking by H. Schmidt-Kanefendt (03.04.2026)
- [`260403_Bestandsaufnahme_DE.md`](stakeholder/260403_Bestandsaufnahme_DE.md) — clean German Markdown extraction
- [`260403_Bestandsaufnahme_EN.md`](stakeholder/260403_Bestandsaufnahme_EN.md) — English translation
- [`NEXT_CHANGES.md`](stakeholder/NEXT_CHANGES.md) — action-item digest (P0–P4), prioritized and grouped into sprints

---

## The headline number

Balance button on Heroku: **3-10 minutes → 0.3-1.4 seconds** (~500-1500× faster on repeat use). Zero math changes. No stakeholder-visible renames.

Details and every measurement: [PERFORMANCE.md](PERFORMANCE.md).
