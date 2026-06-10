# Regression playbook

Claude follows these recipes step-by-step. Each scenario: drive the app via Playwright MCP, capture a JSON of probed values, save to `verification/YYYY-MM-DD/<id>.json`, then run `python regression/compare.py <id>` to diff against `regression/golden/<id>.json`.

## Common setup (every scenario)

1. Ensure stack is up: `docker compose ps` → all three services `Up`. If not, `bash scripts/bootstrap_runtime.sh`.
2. Ensure testsim exists: password in `.claude/test-credentials.json`. Recreate via the snippet there if login fails.
3. `mkdir -p verification/$(date +%F)` — session artifact folder.
4. `mkdir -p regression/screenshots/<scenario-id>` if running in capture mode.

## Scenario A — baseline-readonly

**Mutations:** none. **DB state after:** unchanged.

Steps:
1. `browser_navigate http://localhost:8001/login/`
2. Fill `testsim` / `TestSim!2026`, submit.
3. Confirm URL is `/simulation/`.
4. For each of: `/simulation/`, `/landuse/`, `/renewable/`, `/verbrauch/`, `/annual-electricity/`, `/bilanz/`, `/cockpit/`, `/ws/`:
   - `browser_navigate` to the URL
   - `browser_snapshot` (depth 3 sufficient)
   - Probe: page title (exact string)
   - Probe: any numeric cells with a recognizable `data-code` or aria label
   - `browser_take_screenshot` → capture mode: `regression/screenshots/A-baseline-readonly/<page>.png`; verify mode: `verification/<today>/A-baseline-readonly-<page>.png`
5. Emit JSON to `verification/<today>/A-baseline-readonly.json`:
   ```json
   {
     "pages": {
       "/simulation/": {"title": "...", "probes": {...}},
       ...
     }
   }
   ```
6. `python regression/compare.py A-baseline-readonly` — expect exit 0 in verify mode.

**First run (capture):** copy the emitted JSON to `regression/golden/A-baseline-readonly.json` and commit with the screenshots.

## Scenario C — ws-balance

**Mutations:** triggers a WS balance recalculation (creates a `BalanceJob`, worker consumes it). Resets via `api/baseline/restore/` at the end.

Steps:
1. Login as testsim (same as A).
2. `POST /api/baseline/create/` to establish a restore point.
3. `browser_navigate /annual-electricity/`
4. Capture pre-balance values:
   - Find row `9.3.1` — record value (expected hard-assert: 405047)
   - Find row `9.3.4` — record value (expected hard-assert: 189289)
   - Find row `10.x` totals — record (will change)
5. Trigger WS balance: click the "WS-Speicher ausgleichen" button **or** `POST /api/ws/balance/` directly. Capture returned `job_id` (uuid).
6. Poll `GET /api/ws/balance-job/<job_id>/` every 0.5s until `status == "completed"` or 60s timeout.
7. `browser_navigate /annual-electricity/` (reload) and `browser_navigate /ws/`
8. Capture post-balance values:
   - Row `9.3.1` — MUST still be 405047 (hard assert, not captured)
   - Row `9.3.4` — MUST still be 189289 (hard assert, not captured)
   - Row `9.x` values — capture (golden comparison)
   - Row `10.x` values — capture (golden comparison)
   - `/ws/` page key storage metrics — capture
9. `POST /api/baseline/restore/` to reset DB.
10. Emit JSON to `verification/<today>/C-ws-balance.json`:
    ```json
    {
      "invariants": {"9.3.1": 405047, "9.3.4": 189289},
      "captured": {"annual_electricity": {...}, "ws": {...}}
    }
    ```
11. `python regression/compare.py C-ws-balance`.
12. Verify invariants section matches `regression/golden/C-ws-balance.json.invariants` exactly — if not, FAIL loudly (this is a correctness failure, not a drift).

## Cleanup (every scenario)

- `browser_close`
- `rm -rf .playwright-mcp/`
- Screenshots from verification mode stay in `verification/<today>/` — wiped at end of session.

## Scenario D — full-flow-verbrauch-solar-wind

**Mutations:** 2 Verbrauch edits via browser localStorage → 2 Save & Continue recalcs → Recalculate Renewables → one of two balance-button pairs (Solar or Wind). Balance-job results are transient (DB not persisted); seed auto-restores.

Steps:

1. Login as testsim.
2. Clear `verbrauch_changes_history` and `landuse_changes_history` from localStorage to start clean.
3. **Edit 1.1.2**: Navigate to `/verbrauch/`, click the user-% cell for code `1.1.2` (Zieleinfluss Endanwendungs-Effizienz), change from 95 → **100**, blur.
4. **Save & Continue (round 1)**: Click the **Save All Values** button. Wait for `verbrauch_recalc` BalanceJob to finish (≈ 8 s).
5. Probe `/verbrauch/` rows 7 and 8 — capture `ziel` values for golden comparison.
6. **Edit 2.4.1**: Change code `2.4.1` (Spez.Raumwärmebed. Status/Saniert) from 80 → **75**, blur.
7. **Save & Continue (round 2)**: Click **Save All Values**. Wait for `verbrauch_recalc` (≈ 6 s).
8. Hard-assert: `/verbrauch/` row 7 ziel = **1,006,821.8** and row 8 ziel = **1,858,597.3**.
9. Navigate to `/renewable/`. Click **Recalculate Renewables**. Wait (≈ 8 s, 30 rows updated).
10. Navigate to `/ws/` and run EITHER the solar variant OR the wind variant:

**Solar variant:**
- 10a. Click `#applyBalanceBtn` (WS Balance Solar). Accept confirm + alert dialogs. Wait (≈ 10 s).
- 10b. Capture LU_2.1 → expected **680,825.67 ha** after this step.
- 10c. Click `#applyFullBalanceBtn` (Sector + WS Solar Balance). Accept dialogs. Wait (≈ 68 s).
- 10d. Hard-assert: LU_2.1 = **680,478.26 ha** (tol ±1), `/annual-electricity/` annual = **1,108,834.53 GWh** (tol ±0.5), speicherdrift ≤ 0.1 GWh.

**Wind variant:**
- 10a'. Click `#applyWindBalanceBtn` (WS Balance Wind). Accept dialogs. Wait (≈ 10 s).
- 10b'. Capture LU_6 → expected **715,288.57 ha** (change from baseline is tiny but captured).
- 10c'. Click `#applyWindFullBalanceBtn` (Sector + WS Wind Balance). Accept dialogs. Wait (≈ 45 s).
- 10d'. Hard-assert: LU_6 = **715,288.57 ha** (tol ±1), `/annual-electricity/` annual = **1,108,834.53 GWh** (tol ±0.5), speicherdrift ≤ 0.1 GWh.

11. Emit `verification/<today>/D-full-flow-verbrauch-solar-wind.json` with baseline_fingerprint + captured values for whichever variant(s) ran.
12. `python regression/compare.py D-full-flow-verbrauch-solar-wind`:
    - Exit 0 → OK.
    - Exit 1 → value drift (investigate; maybe intentional, maybe regression).
    - Exit 2 → baseline fingerprint drift (seed changed; re-capture required, don't just patch values).

**Cross-variant invariant** to verify manually when both variants are in the same run: annual electricity converges to the same value (± 0.5 GWh) in both paths.

**Cleanup**: scenario doesn't mutate DB; localStorage is cleared at start. No DB reset needed.

---

## When a diff appears

1. Read the diff output. Which keys changed?
2. Did you intentionally change something that should affect those values? If yes → regenerate golden (capture mode), commit the golden change alongside the code change.
3. If no → you have a regression. Investigate before committing.
4. Never `cp verification/.../A.json regression/golden/A.json` to "make the test pass" without steps 1–3.
