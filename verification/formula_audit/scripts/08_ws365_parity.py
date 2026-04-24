"""§5 WS365 daily time-series parity.

Compare our WSData promille fields to Excel Zeitreihen Kalkulation
columns C/D/E/F for all 365 days.

Also: extract every named range from WS.xlsm and compare to our
WS constants (Formula[category='ws_constant']).

Outputs:
  04_ws365_parity/daily_timeseries_diff.csv
  04_ws365_parity/named_constants.csv
  04_ws365_parity/discrepancies.md
  04_ws365_parity/summary.md
"""
from __future__ import annotations
import os, sys, csv, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landuse_project.settings")
import django
django.setup()

from openpyxl import load_workbook
from simulator.models import Formula
from simulator.ws_models import WSData

SRC = ROOT / "docs" / "100prosim_d_250517_250517.1817m" / "WS.xlsm"
OUT = ROOT / "verification" / "formula_audit" / "04_ws365_parity"
OUT.mkdir(parents=True, exist_ok=True)

def rel(a, b):
    if a is None or b is None:
        return math.inf
    try:
        fa, fb = float(a), float(b)
    except:
        return math.inf
    if fa == 0 and fb == 0:
        return 0.0
    m = max(abs(fa), abs(fb))
    if m < 1e-9:
        return 0.0
    return abs(fa - fb) / m

def verdict(d):
    if d is None: return "NO_DATA"
    if d == math.inf: return "NO_MATCH"
    if d == 0.0: return "EXACT"
    if d < 0.0001: return "PASS_COSMETIC"
    if d < 0.001: return "PASS"
    return "DRIFT"

def main():
    wb = load_workbook(SRC, data_only=True)
    zr = wb["Zeitreihen Kalkulation"]

    # Column mapping (Excel → our field)
    col_map = {
        "wind_promille": "C",
        "solar_promille": "D",
        "heizung_abwaerm_promille": "E",
        "verbrauch_promille": "F",
    }

    out_csv = OUT / "daily_timeseries_diff.csv"
    rows = []
    cols = ["day", "field", "our_value", "excel_cell", "excel_value", "drift", "verdict"]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        # WSData day = 1..365, Excel row = 157..521 (day=1 → row=157)
        for day in range(1, 366):
            xl_row = 157 + (day - 1)
            ws_obj = WSData.all_objects.filter(owner=None, tag_im_jahr=day).first()
            if not ws_obj:
                continue
            for field, col in col_map.items():
                our = getattr(ws_obj, field, None)
                xl_cell = f"{col}{xl_row}"
                xl_val = zr[xl_cell].value
                d = rel(our, xl_val)
                v = verdict(d)
                row = dict(day=day, field=field, our_value=our, excel_cell=xl_cell, excel_value=xl_val, drift=d, verdict=v)
                rows.append(row)
                w.writerow(row)
    print(f"wrote {out_csv} ({len(rows)} rows)")

    # Named constants
    out_c = OUT / "named_constants.csv"
    wb_name = wb  # already loaded
    defnames = list(wb_name.defined_names.keys()) if hasattr(wb_name, "defined_names") else []
    const_rows = []
    with open(out_c, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "excel_ref", "excel_cached_value", "db_formula_key", "db_expression", "match"])
        w.writeheader()
        # Build DB mapping hints
        db_map = {
            "EtaStromGas": "WS_ETA_STROM_GAS",
            "EtaRückverstromung": "WS_ETA_GAS_STROM",
            # Abregelung → WS_ABREGELUNG_THRESHOLD (F006 — mismatch)
            "Abregelung": "WS_ABREGELUNG_THRESHOLD",
        }
        for name in sorted(defnames):
            dn = wb_name.defined_names[name]
            ref = getattr(dn, "attr_text", "")
            # Resolve value
            xl_val = None
            if "!" in ref and "#REF!" not in ref:
                try:
                    sn, cell = ref.split("!", 1)
                    sn = sn.strip("'")
                    cell = cell.replace("$", "")
                    xl_val = wb_name[sn][cell].value
                except Exception:
                    pass
            db_key = db_map.get(name, "")
            db_expr = ""
            if db_key:
                f_obj = Formula.objects.filter(key=db_key).first()
                if f_obj:
                    db_expr = f_obj.expression
            # Classify
            match = ""
            if xl_val is not None and db_expr:
                try:
                    if float(db_expr) == float(xl_val):
                        match = "EXACT"
                    else:
                        match = f"DRIFT db={db_expr} vs xl={xl_val}"
                except:
                    match = "NONNUM"
            const_rows.append({
                "name": name, "excel_ref": ref, "excel_cached_value": xl_val,
                "db_formula_key": db_key, "db_expression": db_expr, "match": match,
            })
            w.writerow(const_rows[-1])
    print(f"wrote {out_c} ({len(const_rows)} rows)")

    # Discrepancies
    from collections import Counter
    verdict_ts = Counter(r["verdict"] for r in rows)
    out_disc = OUT / "discrepancies.md"
    with open(out_disc, "w", encoding="utf-8") as f:
        f.write("# §5 WS365 Daily Time-Series — discrepancies\n\n")
        f.write("## Time-series parity (365 days × 4 input fields = 1460 comparisons)\n\n")
        f.write("Verdict distribution:\n\n")
        for k, v in sorted(verdict_ts.items()):
            f.write(f"- {k}: {v}\n")
        f.write("\n## DRIFT rows (if any)\n\n")
        drift_rows = [r for r in rows if r["verdict"] == "DRIFT"]
        f.write(f"{len(drift_rows)} DRIFT rows.\n\n")
        if drift_rows:
            f.write("| day | field | ours | excel | drift |\n|---|---|---|---|---|\n")
            for r in drift_rows[:50]:
                f.write(f"| {r['day']} | {r['field']} | {r['our_value']} | {r['excel_value']} | {r['drift']:.6f} |\n")

        f.write("\n## Named constants\n\n")
        f.write("| name | excel ref | excel value | DB key | DB expr | match |\n|---|---|---|---|---|---|\n")
        for r in const_rows:
            f.write(f"| {r['name']} | {r['excel_ref']} | {r['excel_cached_value']} | {r['db_formula_key']} | {r['db_expression']} | {r['match']} |\n")

    with open(OUT / "summary.md", "w", encoding="utf-8") as f:
        f.write("# §5 WS365 Daily Time-Series — summary\n\n")
        f.write(f"Compared {len(rows)} cells (365 days × 4 input fields).\n\n")
        f.write("Verdict distribution:\n")
        for k, v in sorted(verdict_ts.items()):
            f.write(f"- {k}: {v}\n")
        f.write(f"\nNamed constants: {len(const_rows)} extracted, see named_constants.csv.\n")

if __name__ == "__main__":
    main()
