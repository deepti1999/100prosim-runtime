# Cross-cutting — region round-trip

**Test goal:** add a synthetic region → switch to it → confirm isolation → switch back to DE → confirm DE byte-identical.

## Status

**NOT RE-RUN in this audit.** Verified via Phase C 2026-04-23 per `DATA_MODEL_IMPORT_AUDIT.md` §0c with a synthetic TEST region cloned DE × 1.05.

## Evidence from Phase C

Phase C V5 on `prosim-100-ce34bbba8419.herokuapp.com` (now destroyed):

1. **Initial state (DE):**
   - /annual-electricity/: pv=1.211.176, wind=706.236, hydro=19.493, bio=4.525
   - Pmax-Ely=194 GW, Pmax-RV=261 GW
   - Abgleichdifferenz=157

2. **TEST region created** via `scripts/heroku_seed_test_region.py` (clones DE × 1.05).

3. **Switch to TEST:**
   - /landuse/ values 5% higher (LU_0=37.547.505 = 35.759.529 × 1.05)
   - /annual-electricity/: pv=1.271.735, wind=741.548, hydro=20.467, bio=4.751
   - Pmax-Ely=200 GW (TEST.installed_pmax_ely_gw), Pmax-RV=270 GW (TEST.installed_pmax_rv_gw)

4. **Switch back to DE:** **byte-identical** to step 1.

Screenshots saved at `verification/phase_c/01-04` (gitignored, not in this audit's screenshots/ tree).

## Verdict

**PASS** — region isolation + bidirectional switch verified end-to-end; DE state is unchanged after a TEST round-trip. The round-trip exercise this audit COULD repeat would require dirtying the current Heroku testsim workspace by re-running `scripts/heroku_seed_test_region.py`. Reusing the prior verification.
