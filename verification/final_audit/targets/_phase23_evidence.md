# §2.3 — shared evidence (Datenmodell: provenance + region)

## PDF source
§2.3 (page 3) decomposes into §2.3.1 Nachvollziehbarkeit (T8-T10) and §2.3.2 Alternativ-Regionen (T11-T13). PDF text recorded in `pdf_text/portierung_bestandsaufnahme.txt` lines 84-116.

PDF framing is **Vorschlag** (proposal) — "Schnittstelle zur Nutzung der bestehenden Excel-Datenmodell-Dateien". Per `260403_Section_2.3_decision.md`, we ship the *properties* (traceability, multi-region, admin-edit), not necessarily the live-Excel-binding mechanism.

## Implementation timeline

| Phase | T-IDs | Date | Commits |
|---|---|---|---|
| Phase A | T8, T9, T10 | 2026-04-23 | `bb62a49`…`9da1a22` (9 commits) |
| Phase B | T11, T12, T13 (architecture) | 2026-04-23 | `4fc6faf`…`a7174ea` (9 commits) |
| Phase C | T11, T12, T13 (operational) | 2026-04-23 | `e23653b`…`51f50cd` (8 commits) |

## V2 — tests
| Module | Tests | Phase |
|---|---|---|
| `test_wb_provenance_schema` | 11/11 | A |
| `test_wb_excel_provenance_import` | 13/13 | A |
| `test_wb_region_model` | 12/12 | B |
| `test_wb_region_fk` | 14/14 | B |
| `test_wb_workspace_region` | 11/11 | B |
| `test_wb_region_middleware` | 6/6 | B |
| `test_wb_region_switcher` | 12/12 | B |
| `test_wb_excel_import_region` | 6/6 | B |
| `test_wb_pmax_dynamic` | 8/11 (3 env-skip) | B |
| `test_wb_geb_region_uniq` | 4/4 | C |
| `test_wb_snapshot_region` | 4/4 | C |
| `test_wb_balance_region_routing` | 4/4 | C |
| `test_wb_wsdata_region` | 8/8 | C |
| `test_wb_import_create_region` | 4/4 | C |

Total §2.3 V2: 109 dedicated tests (excluding 3 env-skip), all green per `cross_cutting/test_suite_full.md`.

## V4 / V5 — visual evidence

**Phase A (T8/T9):** info-icon "i" badge per row of /landuse/ /renewable/ /verbrauch/ /gebaeudewarme/. Visible as the "Q" column in `screenshots/{localhost,heroku}/02_landuse.png` + `03_renewable.png` + `05_gebaeudewaerme.png`. Click opens Bootstrap popover with origin badge + source URL link + assumption text. (Popover content not opened in this audit's static screenshots; verified previously per `DATA_MODEL_IMPORT_AUDIT.md` §0a "popovers render on prosim-100-2c767e32f236".)

**Phase B (T11):** "DE" region dropdown visible in nav top-right of every captured page (with globe icon). Dropdown opens to show "DE | Deutschland" entry. Switching is wired (verified per Phase C V5 with synthetic TEST region).

**Phase C (T11/T12/T13):** synthetic TEST region cloned DE × 1.05 was verified previously per `DATA_MODEL_IMPORT_AUDIT.md` §0c — TEST values visibly differ from DE on /landuse/ + /annual-electricity/; D4a/D4b read TEST's installed_pmax_* (200 GW / 270 GW); switching back to DE yields byte-identical baseline values. Verification screenshots in `verification/phase_c/01-04`.

## Edge cases
- **No D.xlsx for region:** import command fails loud per `test_wb_excel_provenance_import::test_missing_file_fails_loud`.
- **Region without seed rows:** Phase C row-creating mode handles via `_create_region_rows_from_de_template` (test_wb_import_create_region).
- **Region switch mid-session:** thread-local `region_scope` ensures the worker uses the right region for cross-process cache invalidation.

## Verdict per target
- T8 PASS · T9 PASS · T10 PASS-WITH-CAVEAT (CLI-only update, no GUI)
- T11 PASS · T12 PASS · T13 PASS-WITH-CAVEAT (CLI shell incantation, no GUI as PDF "spezielle Admin-Rechte sind nicht erforderlich" reads)

§2.3 is the most heavily-tested phase in this audit (109 dedicated unit tests + 3 phases of integrated V5 verification). Operational closure was validated end-to-end via Phase C synthetic TEST region.
