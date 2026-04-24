"""Refine DIFFERENT verdicts by pattern-categorizing.

Many Round 2 'DIFFERENT' rows are numerically equivalent but
structurally different:
  SUM_REORDER: DB sums in different operand order (a+b+c vs c+a+b)
  SUMIF_VS_DIRECT: DB references a single code, Excel uses SUMIF to aggregate
  PCT_DIVISOR: DB uses '/100', Excel uses '%' shorthand (same)
  CELLREF_VS_TOKEN: DB uses Python-style token (Renewable_X), Excel uses cell ref
  MAPPING_MISMATCH: The curated mapping pointed to the wrong Excel cell
  REAL_DIFF: Genuinely different formulas
"""
from __future__ import annotations
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIFF_CSV = ROOT / "verification" / "formula_audit_full" / "02_full_formula_parity" / "per_formula_diff.csv"

def categorize(row):
    db = (row.get("db_expression") or "").strip()
    xl = (row.get("excel_formula") or "").strip()
    if xl.startswith("="):
        xl = xl[1:]

    # Count operands + operators
    def tokens(s):
        s = s.replace("$", "").replace(" ", "")
        return re.findall(r"[A-Za-z_][A-Za-z_0-9\.]*|\d+(?:\.\d+)?|[+\-*/(),]", s)

    db_toks = tokens(db)
    xl_toks = tokens(xl)
    db_ops = [t for t in db_toks if t in "+-*/"]
    xl_ops = [t for t in xl_toks if t in "+-*/"]
    db_vars = [t for t in db_toks if re.match(r"[A-Za-z_][A-Za-z_0-9\.]*$", t)]
    xl_vars = [t for t in xl_toks if re.match(r"[A-Za-z_][A-Za-z_0-9\.]*$", t)]

    # SUMIF
    if "SUMIF" in xl.upper() and not db.upper().startswith("SUMIF"):
        return "SUMIF_VS_DIRECT", "Excel uses SUMIF aggregation; DB references a single code (likely the same aggregate)"

    # '%' shorthand in Excel
    if "%" in xl and "/ 100" not in db and "*100" not in db and "/100" not in db.replace(" ", ""):
        if db.count("*") + db.count("/") == xl.count("*") + xl.count("/") + 1:
            # DB has one extra op (the /100 or *100 explicit); Excel uses %
            return "PCT_SHORTHAND", "Excel '%' shorthand vs explicit '/100' in DB (equivalent)"

    # Sum operand reorder
    if sorted(db_ops) == sorted(xl_ops) and sorted(db_ops) == ["+"] * len(db_ops):
        # Both are sums; check if operand count matches
        if len(db_vars) == len(xl_vars):
            return "SUM_REORDER", f"Sum of {len(db_vars)} operands in different order"

    # Same structural shape (operators match exactly)
    if db_ops == xl_ops:
        return "CELLREF_VS_TOKEN", "Same operator sequence; DB uses Python tokens (Renewable_X), Excel uses cell refs"

    # Unequal structure but operands overlap
    return "REAL_DIFF", f"DB_ops={''.join(db_ops)} XL_ops={''.join(xl_ops)}; investigate"

def main():
    with open(DIFF_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Add `diff_category` column
    fieldnames = list(rows[0].keys())
    if "diff_category" not in fieldnames:
        fieldnames.append("diff_category")
        fieldnames.append("diff_note")

    for row in rows:
        if row["verdict"] != "DIFFERENT":
            row["diff_category"] = ""
            row["diff_note"] = ""
            continue
        cat, note = categorize(row)
        row["diff_category"] = cat
        row["diff_note"] = note

    with open(DIFF_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)

    # Summary of categories
    from collections import Counter
    c = Counter(r["diff_category"] for r in rows if r["verdict"] == "DIFFERENT")
    print(f"DIFFERENT categorization ({sum(c.values())} total):")
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
