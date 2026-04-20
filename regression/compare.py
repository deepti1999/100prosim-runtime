#!/usr/bin/env python3
"""Diff a current-run JSON against its golden. Exit 0 on match, 1 on diff."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO / "regression" / "golden"


def _find_current(scenario_id: str) -> Path:
    candidates = sorted((REPO / "verification").glob(f"*/{scenario_id}.json"))
    if not candidates:
        raise SystemExit(f"No current-run JSON for scenario '{scenario_id}' under verification/")
    return candidates[-1]


def _flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _flatten(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def _check_baseline_fingerprint(golden: dict, current: dict) -> list:
    """If the golden has a baseline_fingerprint, the current run must match it
    or the scenario's expected values are invalid. Return list of mismatches."""
    g_fp = golden.get("baseline_fingerprint")
    c_fp = current.get("baseline_fingerprint")
    if not g_fp:
        return []  # scenarios without fingerprints (legacy) skip this check
    if not c_fp:
        return [("baseline_fingerprint", g_fp, "<missing in current run>")]
    mism = []
    for key, gv in g_fp.items():
        if key == "note":
            continue
        cv = c_fp.get(key)
        if cv != gv:
            try:
                if gv is not None and cv is not None and abs(float(gv) - float(cv)) < 1e-6:
                    continue
            except Exception:
                pass
            mism.append((f"baseline_fingerprint.{key}", gv, cv))
    return mism


def diff(scenario_id: str) -> int:
    golden_path = GOLDEN_DIR / f"{scenario_id}.json"
    if not golden_path.exists():
        raise SystemExit(f"No golden for '{scenario_id}' at {golden_path}")
    current_path = _find_current(scenario_id)

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    current = json.loads(current_path.read_text(encoding="utf-8"))

    fp_mism = _check_baseline_fingerprint(golden, current)
    if fp_mism:
        print(f"FINGERPRINT_DRIFT {scenario_id}: baseline has changed — expected values invalid")
        print(f"  golden:  {golden_path}")
        print(f"  current: {current_path}")
        for key, gv, cv in fp_mism:
            print(f"  {key}\n    golden  = {gv!r}\n    current = {cv!r}")
        print("  -> re-capture this scenario's golden before comparing values.")
        return 2  # distinct exit code for baseline drift vs value drift

    g = dict(_flatten(golden))
    c = dict(_flatten(current))

    mismatches = []
    for key in sorted(set(g) | set(c)):
        if key not in g:
            mismatches.append((key, "<missing>", c[key]))
        elif key not in c:
            mismatches.append((key, g[key], "<missing>"))
        elif g[key] != c[key]:
            mismatches.append((key, g[key], c[key]))

    if not mismatches:
        print(f"OK {scenario_id}: current matches golden ({len(g)} fields)")
        return 0

    print(f"DIFF {scenario_id}: {len(mismatches)} mismatches")
    print(f"  golden:  {golden_path}")
    print(f"  current: {current_path}")
    for key, gv, cv in mismatches:
        print(f"  {key}\n    golden  = {gv!r}\n    current = {cv!r}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python regression/compare.py <scenario_id>")
    sys.exit(diff(sys.argv[1]))
