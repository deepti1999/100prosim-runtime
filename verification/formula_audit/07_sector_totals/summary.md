# §8 Sector Totals Parity — summary

## Headline

Sector total parity (sum of all energy carriers per sector) is
**mostly excellent**:

| sector | engine | Excel H25/K25/N25/Q25 | drift | verdict |
|--------|-------:|---------------------:|------:|---------|
| KLIK | 329,346 | 329,214 | 0.04 % | PASS_COSMETIC |
| GW | 799,187 | 798,867 | 0.04 % | PASS_COSMETIC |
| PW | 550,371 | 555,395 | 0.90 % | DRIFT (F004) |
| MA | 753,713 | 753,713 | ≈ 0 | **EXACT** ✓ |
| **TOTAL** | 2,432,616 | 2,437,189 | **0.19 %** | **PASS** ✓ |

## Key insight

**Sector-level totals are correct** (the engine's `verbrauch_gesamt`
uses `V_1.4`, `V_2.10`, `V_3.7`, `V_6.0` — all aggregate codes that
Excel computes independently). **Per-energy-carrier sub-splits are
not**.

This is important: when Pascal looks at the "Verbrauch gesamt"
total on /bilanz/, the numbers are right. When a reader drills into
"Strom" vs "Fuels" vs "Heat" per sector, that's where F007 (GW Strom = 0) and F008 (MA Strom 84 %) manifest.

## Per-sector files

- `KLIK.md` — PASS_COSMETIC on total; renewable/fossil split drifts 1.2 %.
- `Gebaeudewaerme.md` — PASS_COSMETIC on total; GW Strom = 0 (F007).
- `Prozesswaerme.md` — 0.90 % DRIFT on total (F004); PW Strom 6.85 % short.
- `Mobile_Anwendungen.md` — **EXACT** on total; MA Strom 84 % off (F008, but V_6.1 + V_6.2 reconciles to correct total).

## Findings cross-reference

- F004 — PW total 0.9 % short (was identified in §4)
- F007 — GW Strom = 0 (critical, from §4)
- F008 — MA Strom 84 % internal split error (from §4)

No new findings from §8. Confirms the §4 story at a different level
of granularity.

## Self-skepticism

- [x] Compared all 4 sectors
- [x] Drilled down by energy carrier (Strom / Fuels / Heat / total)
- [x] Connected to existing F007/F008
- [x] Explained the discrepancy between total-OK and sub-split-off
      (uses different DB codes: aggregates vs sub-subcodes)
- [x] Did not rubber-stamp: PW 0.9 % is legit DRIFT, not acceptable
      cosmetic

## Artifacts

- `KLIK.md`, `Gebaeudewaerme.md`, `Prozesswaerme.md`, `Mobile_Anwendungen.md`
