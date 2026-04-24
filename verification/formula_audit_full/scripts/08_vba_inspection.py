"""§07 VBA inspection — extract and analyze macros from all .xlsm files.

Uses olevba from oletools to extract VBA module text. Scans for:
  - Workbook_Open, Auto_Open, Workbook_BeforeSave, Worksheet_Change
  - Cell mutator assignments (Range/Cells .Value = ...)
  - Application.Calculate / ActiveSheet.Calculate
  - External I/O

Outputs:
  07_vba_inspection/extracted_modules/<file>_<module>.txt
  07_vba_inspection/findings.md
  07_vba_inspection/summary.md
"""
from __future__ import annotations
import re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "100prosim_d_250517_250517.1817m"
OUT = ROOT / "verification" / "formula_audit_full" / "07_vba_inspection"
OUT.mkdir(parents=True, exist_ok=True)
MOD_DIR = OUT / "extracted_modules"
MOD_DIR.mkdir(exist_ok=True)

XLSM_FILES = sorted(DOCS.glob("*.xlsm"))

def extract_vba(path):
    """Use olevba to extract VBA modules. Returns dict module_name -> text."""
    try:
        from oletools.olevba import VBA_Parser
    except ImportError:
        return {}, "oletools not installed"
    try:
        p = VBA_Parser(str(path))
        if not p.detect_vba_macros():
            return {}, "no VBA macros"
        modules = {}
        for (filename, stream_path, vba_filename, vba_code) in p.extract_macros():
            modules[vba_filename or stream_path] = vba_code or ""
        return modules, None
    except Exception as e:
        return {}, f"error: {e}"


# Patterns to flag
FLAG_PATTERNS = {
    "on_open": re.compile(r"\b(Workbook_Open|Auto_Open|Document_Open)\b", re.IGNORECASE),
    "on_save": re.compile(r"\bWorkbook_BeforeSave\b", re.IGNORECASE),
    "on_change": re.compile(r"\b(Workbook_SheetChange|Worksheet_Change)\b", re.IGNORECASE),
    "cell_mutator": re.compile(r"(Range\s*\(.+?\)|Cells\s*\(.+?\))\s*\.\s*Value\s*=", re.IGNORECASE),
    "calc_trigger": re.compile(r"(Application\.Calculate|\.Calculate\s*$)", re.IGNORECASE | re.MULTILINE),
    "external_io": re.compile(r"\b(Open\s+\".+\"\s+For|URLDownloadToFile|Shell\s*\()", re.IGNORECASE),
    "password_protect": re.compile(r"\bProtect\s*\(?Password", re.IGNORECASE),
}


def scan_module(name, code):
    """Return list of (pattern_name, line_number, line_text) hits."""
    hits = []
    for pat_name, pat in FLAG_PATTERNS.items():
        for m in pat.finditer(code):
            # Find line number
            prefix = code[:m.start()]
            ln = prefix.count("\n") + 1
            # Get full line
            lines = code.split("\n")
            line_text = lines[ln - 1] if ln <= len(lines) else ""
            hits.append((pat_name, ln, line_text.strip()))
    return hits


def main():
    file_results = {}
    for path in XLSM_FILES:
        print(f"scanning {path.name}...")
        modules, err = extract_vba(path)
        if err:
            file_results[path.name] = {"error": err, "modules": {}, "hits": []}
            continue
        # Write extracted modules to disk
        all_hits = []
        for mod_name, code in modules.items():
            safe_mod = re.sub(r"[^\w.-]+", "_", mod_name)[:80]
            out_file = MOD_DIR / f"{path.stem}__{safe_mod}.txt"
            with open(out_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(code or "")
            hits = scan_module(mod_name, code)
            for (pat_name, ln, text) in hits:
                all_hits.append({
                    "module": mod_name, "pattern": pat_name,
                    "line": ln, "text": text[:200]
                })
        file_results[path.name] = {
            "error": None,
            "modules": list(modules.keys()),
            "hits": all_hits,
            "module_count": len(modules),
        }

    # Write summary + findings
    with open(OUT / "summary.md", "w", encoding="utf-8") as f:
        f.write("# §07 VBA inspection — summary\n\n")
        f.write(f"Scanned {len(XLSM_FILES)} .xlsm files.\n\n")
        f.write("| file | modules | hits | error |\n|------|--------:|-----:|-------|\n")
        for name, res in file_results.items():
            f.write(f"| {name} | {res.get('module_count', 0)} | {len(res.get('hits', []))} | {res.get('error') or '—'} |\n")

    # Findings
    with open(OUT / "findings.md", "w", encoding="utf-8") as f:
        f.write("# §07 VBA Inspection — findings\n\n")
        total_hits = sum(len(r["hits"]) for r in file_results.values())
        f.write(f"Total pattern hits across all files: {total_hits}\n\n")
        for name, res in file_results.items():
            if not res["hits"]:
                continue
            f.write(f"\n## {name}\n\n")
            # Group by pattern
            from collections import defaultdict
            by_pat = defaultdict(list)
            for h in res["hits"]:
                by_pat[h["pattern"]].append(h)
            for pat_name in ["on_open", "on_save", "on_change", "cell_mutator", "calc_trigger", "external_io", "password_protect"]:
                if pat_name not in by_pat:
                    continue
                hits = by_pat[pat_name]
                f.write(f"\n### {pat_name} — {len(hits)} hits\n\n")
                for h in hits[:20]:
                    f.write(f"- `{h['module']}` line {h['line']}: `{h['text']}`\n")
                if len(hits) > 20:
                    f.write(f"\n(+ {len(hits) - 20} more)\n")

    print(f"\nwrote {OUT / 'summary.md'}")
    print(f"wrote {OUT / 'findings.md'}")
    print(f"extracted modules -> {MOD_DIR}")

if __name__ == "__main__":
    main()
