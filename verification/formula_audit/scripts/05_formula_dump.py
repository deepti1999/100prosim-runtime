"""Dump all 760 Formula rows + all WS365Formula rows to CSV.

Also emit a tabular summary grouped by category, formula_type, ws_row_type.
"""
from __future__ import annotations
import os, sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landuse_project.settings")
import django
django.setup()

from simulator.models import Formula
from simulator.ws_models import WS365Formula

OUT = ROOT / "verification" / "formula_audit" / "02_formula_parity"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    out_f = OUT / "formula_table_dump.csv"
    cols = ["table", "key", "category", "formula_type", "ws_row_type", "is_fixed", "expression", "description"]
    with open(out_f, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in Formula.objects.all().order_by("category", "key"):
            w.writerow({
                "table": "Formula",
                "key": row.key,
                "category": row.category,
                "formula_type": row.formula_type,
                "ws_row_type": row.ws_row_type,
                "is_fixed": row.is_fixed,
                "expression": row.expression,
                "description": row.description or "",
            })
    # Append WS365Formula
    out_ws = OUT / "ws365_formula_dump.csv"
    with open(out_ws, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["column_name", "stage", "order", "expression", "description"])
        w.writeheader()
        for row in WS365Formula.objects.all().order_by("order"):
            w.writerow({
                "column_name": row.column_name,
                "stage": row.stage,
                "order": row.order,
                "expression": row.expression,
                "description": row.description or "",
            })
    print(f"wrote {out_f} ({Formula.objects.count()} rows)")
    print(f"wrote {out_ws} ({WS365Formula.objects.count()} rows)")

if __name__ == "__main__":
    main()
