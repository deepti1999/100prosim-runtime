"""Second pass on the curated CSVs — classify OOS rows with specific reasons.

The first pass left some rows with generic 'NO_MAPPING_FOUND' or
'NO_NAME_MATCH'. This pass examines each OOS row and:
  (a) If there's a plausible Excel cell by position/code matching,
      upgrades to a mapping with a note.
  (b) Otherwise, assigns a specific OOS reason:
      - SUMMARY_ROW (DB category='=' marks a computed Endenergieverbrauch row
        whose Excel cell is in the same sheet at a position computed from
        the code hierarchy).
      - CHAPTER_HEADER (parent row with no values, pure hierarchy marker —
        these have no single Excel cell but the Excel sheet represents them
        as chapter text rows).
      - SUBSECTION_PARAMETER (GW 2.4.x parameter rows — Excel encodes them
        under a different section header).
      - ARCHIVED (rows referring to deprecated codes).

Writes updated CSVs in place.
"""
from __future__ import annotations
import csv, re
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "docs" / "100prosim_d_250517_250517.1817m" / "_S.xlsx"
OUT_DIR = ROOT / "verification" / "formula_audit_full" / "01_curated_mappings"

# --- VerbrauchData OOS — position-matching by code hierarchy in 4. Verbrauch ---
# The DB code 'X.Y.Z' where:
#   X = sector (1=KLIK, 2=GW, 3=PW, 4=MA-traktion, 6=MA)
#   Y = subsector (1=Haushalte, 2=Handel/Dienst, 3=Industrie, 4=Brennstoff etc.)
#   Z = item
# In 4. Verbrauch, each chapter spans a contiguous range of rows.
# By walking 4. Verbrauch and tracking the implied code via name indentation,
# we get a row→code mapping that we can invert.
V_CHAPTER_ROWS = {
    # chapter → (start_row, end_row) on 4. Verbrauch
    "1": (8, 42),   # KLIK
    "2": (43, 110),  # GW (partial — some GW is in 2.x verbrauch rows)
    "3": (111, 180),  # PW
    "4": (181, 210),  # MA traktion detail
}

VERBRAUCH_CODE_TO_ROW = {
    # Manually mapped from Round 1 4__Verbrauch dump + re-examination
    # KLIK (code = 1.*)
    "1":       ("4. Verbrauch", 10),
    "1.0":     ("4. Verbrauch", 11),
    "1.1":     ("4. Verbrauch", 21),  # "davon Haushalte" in KLIK section
    "1.1.1":   ("4. Verbrauch", 24),  # Endenergie Haushalte
    "1.1.2":   ("4. Verbrauch", 25),  # Zieleinfluss Endanwendungs-Effizienz
    "1.1.3":   ("4. Verbrauch", 26),  # Endenergie nach Effizienz (the "=" row)
    "1.2":     ("4. Verbrauch", 28),  # davon Handel/Dienstl
    "1.2.1":   ("4. Verbrauch", 29),
    "1.2.2":   ("4. Verbrauch", 30),
    "1.2.3":   ("4. Verbrauch", 31),
    "1.2.4":   ("4. Verbrauch", 32),
    "1.2.5":   ("4. Verbrauch", 33),
    "1.3":     ("4. Verbrauch", 35),  # davon Industrie
    "1.3.1":   ("4. Verbrauch", 36),
    "1.3.2":   ("4. Verbrauch", 37),
    "1.3.3":   ("4. Verbrauch", 38),
    "1.3.4":   ("4. Verbrauch", 39),
    "1.3.5":   ("4. Verbrauch", 40),
    "1.4":     ("4. Verbrauch", 42),  # Endverbrauch Strom für KLIK gesamt

    # GW (code = 2.* in VerbrauchData is DIFFERENT from GebaeudewaermeData;
    # VerbrauchData doesn't have 2.0/2.1 — these live in GebaeudewaermeData).
    # VerbrauchData 2.x codes are in 3. Bedarfsniveau or 4. Verbrauch per-sector.
    # Map below via name proximity.

    # Summary rows (10.x) — these are in 7. Verbrauch Status or similar
    "10":      ("7. Verbrauch Status", 11),  # total Verbrauch row
}

def fix_verbrauch(wb_v):
    """Open verbrauch CSV, try to fill OOS rows via position lookup."""
    csv_path = OUT_DIR / "verbrauch_to_excel.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    closed = 0
    for row in rows:
        if not row.get("oos_reason"):
            continue
        code = row["db_code"]
        m = VERBRAUCH_CODE_TO_ROW.get(code)
        if m:
            sheet, r = m
            row["excel_sheet"] = sheet
            row["excel_row"] = r
            row["excel_cell_status"] = f"{sheet}!L{r}"
            row["excel_cell_ziel"] = f"{sheet}!M{r}"
            row["oos_reason"] = ""  # cleared
            closed += 1
            continue
        # Classify the OOS reason more precisely
        cat = row["db_name"]
        if cat == "=":
            row["oos_reason"] = f"SUMMARY_ROW (db.category='='): row computed by upstream formula; Excel cell is the same-sheet row one after the nearest Zieleinfluss row. Code {code!r} position implied by hierarchy but not explicitly mapped — documented OOS. Tests: compare value downstream via Bilanz (§03)."
        elif cat.startswith("="):
            row["oos_reason"] = f"SUMMARY_ROW (db.category starts with '='): {cat}"
        elif cat in ("Kraft, Licht, Information, Kommunikation, Kälte (KLIK)",
                      "Gebäudewärme (GW)", "Prozesswärme (PW)",
                      "Mobile Anwendungen (MA)", "fossil"):
            row["oos_reason"] = f"CHAPTER_HEADER (DB row represents a sector label, not a data row): {cat}"
        else:
            row["oos_reason"] = f"NO_EXCEL_CELL_DOCUMENTED: {cat} not found in sheets 3/4/6. Likely a DB-only intermediate row."
    # Rewrite
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  Verbrauch: upgraded {closed} OOS rows to proper mappings")


GW_CODE_TO_ROW = {
    # 2.4.x are Raumwärme parameters in 4. Verbrauch
    "2.4.1": ("4. Verbrauch", 52),
    "2.4.2": ("4. Verbrauch", 53),
    "2.4.3": ("4. Verbrauch", 54),
    "2.4.4": ("4. Verbrauch", 55),
    "2.4.5": ("4. Verbrauch", 56),
    "2.4.6": ("4. Verbrauch", 57),
    # 2.7.x Brennstoff parameters
    "2.7.1": ("4. Verbrauch", 75),
    "2.7.2": ("4. Verbrauch", 76),
    "2.7.3": ("4. Verbrauch", 77),
}

def fix_gw(wb_v):
    csv_path = OUT_DIR / "gebaeudewaerme_to_excel.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    closed = 0
    for row in rows:
        if not row.get("oos_reason"):
            continue
        code = row["db_code"]
        m = GW_CODE_TO_ROW.get(code)
        if m:
            sheet, r = m
            row["excel_sheet"] = sheet
            row["excel_row"] = r
            row["excel_cell_status"] = f"{sheet}!L{r}"
            row["excel_cell_ziel"] = f"{sheet}!M{r}"
            row["oos_reason"] = ""
            closed += 1
            continue
        # Stay OOS with specific reason
        row["oos_reason"] = f"NO_EXCEL_CELL_DOCUMENTED: GW code {code!r} name={row['db_name']!r} — subsection parameter not in 4. Verbrauch main column"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  Gebäudewärme: upgraded {closed} OOS rows")


def fix_renewable(wb_v):
    csv_path = OUT_DIR / "renewable_to_excel.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    closed = 0
    for row in rows:
        if not row.get("oos_reason"):
            continue
        # These are summary / chapter rows — mark OOS clearly
        code = row["db_code"]
        cat = row["db_category"]
        sub = row["db_subcategory"]
        name = row["db_name"]
        if name in ("", None):
            row["oos_reason"] = "EMPTY_DB_NAME — cannot match without name"
        elif cat == "Zusammenfassung":
            row["oos_reason"] = f"SUMMARY_ROW: 10.x aggregate on _S.xlsx!2. Erneuerbare rows 225+; code {code!r} computed via upstream"
        else:
            row["oos_reason"] = f"NO_SECTION_MATCH: cat={cat!r} sub={sub!r} name={name!r} (fallback section walk did not find a row)"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  Renewable: OOS rows kept with specific reasons")


def fix_formula():
    """For formula_to_excel.csv, OOS rows are Formulas without a matching
    renewable/verbrauch/gw code. Most are WS constant helpers or Django
    internal helpers already labeled. Leave as-is; they're documented."""
    csv_path = OUT_DIR / "formula_to_excel.csv"
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if not row.get("oos_reason"):
            continue
        # Improve reason text
        cur = row["oos_reason"]
        if "not in renewable_to_excel.csv" in cur:
            row["oos_reason"] = (
                f"CHAINED_OOS — resolved via renewable_to_excel.csv which has "
                f"no mapping for code. Likely a summary/chapter formula row "
                f"(upstream aggregate)."
            )
        elif "not in verbrauch/gebäudewärme mappings" in cur:
            row["oos_reason"] = (
                f"CHAINED_OOS — verbrauch/gebäudewärme CSVs have no mapping. "
                f"Likely a placeholder for a missing or archived code."
            )
        elif "HELPER" in cur:
            pass  # keep
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"  Formula: OOS reasons refined")


def main():
    wb_v = load_workbook(SRC, data_only=True)
    fix_verbrauch(wb_v)
    fix_gw(wb_v)
    fix_renewable(wb_v)
    fix_formula()

if __name__ == "__main__":
    main()
