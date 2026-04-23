# T6 — Acid-test benchmark script

## PDF source
**Section:** §2.2 Antwortzeiten (page 2)
**Lines (extract):** 67–79 of `pdf_text/portierung_bestandsaufnahme.txt`

## German (canonical)
> *"Praxistaugliche Antwortzeiten sind Grundvoraussetzung für die Einsatzfähigkeit. Nach der Installation auf einer leistungsfähigen Rechnerplattform ist deshalb als erstes die damit erreichbare Antwortzeit zu testen. … Dieser Test wird damit zur Nagelprobe für die Einsatzfähigkeit von 100prosim-Web im aktuellen Stand. Falls so keine praxistauglichen Antwortzeiten erreicht werden, müsste die Software-Architektur überprüft und überarbeitet werden."*

The acid-test case itself: *"Im Basis-Szenario wird die Onshore-Windparkfläche von 2,0% auf 2,3% erhöht und die Offshore-Leistung von 70 GW auf 60 GW vermindert. Der Abgleich dauert in 100prosim-Excel 5,8 Sekunden, in 100prosim-Web 120 Sekunden, also die 20-fache Antwortzeit."*

## English
> *"Practically usable response times are a precondition for operational usability. After installation on a performant compute platform, the first thing to test is the response time achievable there. … This test therefore becomes the acid test for whether 100prosim-Web in its current state is fit for deployment. If practically usable response times cannot be reached that way, the software architecture will have to be reviewed and reworked."*

Acid case: onshore 2.0 % → 2.3 %, offshore 70 GW → 60 GW; Excel reference 5.8 s vs Web 120 s.

## Atomic ask T6 satisfies
**T6** is **implied**, not literal — the PDF describes the test case but does not literally say "build a script". `IMPLEMENTATION_PLAN.md` §3 records it as:

> "Acid-test benchmark script (reproducible, tracked cycle-over-cycle) | implied | 0-C"

i.e. an executable harness that future Heroku/ErnES cycles can re-run to measure progress against the 5.8 s Excel reference.

## Acceptance criteria (from `IMPLEMENTATION_PLAN.md` §5 0-C)

> *"Deliverable: `scripts/bench_acid_test.sh` — reproducible 100prosim-Excel-vs-Web response-time comparison per §2.2 (T6). Creates clean workspace state, applies the two changes, triggers Balance Solar, times end-to-end. Runs against any `BASE_URL` (localhost or Heroku). Output: JSON with `{timestamp, url, host_platform, elapsed_s, commit_sha}`."*

Required for full PASS:
1. Script exists at `scripts/bench_acid_test.sh`.
2. Reads `BASE_URL` env var.
3. Logs in as testsim, resets workspace, applies the two changes, triggers Balance Solar, polls until done, captures elapsed time.
4. Appends one JSON object per run to `docs/stakeholder/BENCHMARK_LOG.md`.
5. JSON contains the 5 fields above.
