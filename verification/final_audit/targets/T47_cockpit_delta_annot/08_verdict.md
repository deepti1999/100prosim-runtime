# T47 — Verdict: **FAIL** (downgraded from PASS-WITH-CAVEAT 2026-04-24)

"Prozentuale Veränderung Ziel ggü. Status je Sektor" table is present in 07_cockpit.png with column headers Sektor / Verbrauch Status / Verbrauch Ziel / Δ Verbrauch / Erneuerbare Status / Erneuerbare Ziel / Δ Erneuerbare. **`<tbody>` is empty** because the JS that populates it never runs.

**Same root cause as T43.** See `verification/final_audit/cockpit_charts_root_cause.md`. Bug task #111.
