# §07 VBA Inspection — summary

## Scope

All 3 `.xlsm` files in `docs/100prosim_d_250517_250517.1817m/`:

| file | role | modules | pattern hits | status |
|------|------|--------:|-------------:|--------|
| `_100prosim.xlsm` | launcher | 4 | 1 (Workbook_Open) | harmless |
| `AH.xlsm` | archive / Historie | 23 | 31 (mostly commented-out dead code) | harmless |
| `WS.xlsm` | WS365 energy engine | 16 | 2 (both commented out) | harmless |

## Findings analyzed

### `_100prosim.xlsm` — `Workbook_Open()` calls `Makro1`

`Makro1` opens the 4 companion workbooks (AH, _S, D, WS) via
`Workbooks.Open FileName:=Dateipfad, UpdateLinks:=0`. No cell
assignments in the data sheets. No parity impact — our Python
pipeline reads the data sheets directly.

### `AH.xlsm` — scenario archive macros

- `Modul1.bas` `Range("Archiviert").Value = 0/1/2`: sets the
  `Archiviert` named range (on `AH.xlsm!Cockpit2`). Flag internal
  to AH's archive cycle.
- `Modul1.bas` `Range("MonSzenKenn")` / `Range("AE5")`: AH-internal
  metadata (scenario key, scenario label). Within AH.xlsm only.
- `Step2.bas` `Application.Calculate`: forces recompute in AH.xlsm
  after loading a scenario. Does not affect _S.xlsx or WS.xlsm.
- `Modul1.bas` / `Modul2.bas` `Sheets("Monitor").Protect Password:="m"`:
  password-protects the AH Monitor sheet. Not used by our app.
- `Modul4.bas` has ~13 cell assignments all prefixed with `'`
  (comments) — dead code.

No parity impact: all live macros operate on AH.xlsm's internal
state. Our app doesn't read AH.xlsm for values.

### `WS.xlsm` — 2 hits, both commented out

- `Tabelle10.cls` line 24 / 26: `' Range("AL1").Value = Datum1` and
  `' Range("AM1").Value = Zeit1` — both commented.

No active VBA mutators in WS.xlsm. The workbook is purely
formula-driven.

## Conclusion — no VBA finding

- No macro modifies cells in `_S.xlsx` or `WS.xlsm`. Our pipeline's
  use of cached values via openpyxl is therefore correct.
- The commented-out dead code in Modul4 (13 lines) suggests an
  earlier AH version had live mutators that were retired. Current
  state is clean.
- Password-protected sheet (`AH.xlsm!Monitor`) with trivial password
  "m" — not in our pipeline.

## Completeness attestation

- [x] All 3 `.xlsm` files scanned. No `.xlsb` files present.
- [x] All modules extracted to `extracted_modules/` for review (43 files).
- [x] Seven pattern classes checked: on_open / on_save / on_change /
      cell_mutator / calc_trigger / external_io / password_protect.
- [x] Every pattern hit documented in `findings.md` with file,
      module, line number, and text.
- [x] Active vs commented-out distinguished.
- [x] No CANNOT_VERIFY state (olevba succeeded on all 3 files).

## Artifacts

- `extracted_modules/` — 43 decoded VBA module text files
- `findings.md` — every pattern hit with line/text
- `summary.md` — this file
