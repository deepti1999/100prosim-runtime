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


def diff(scenario_id: str) -> int:
    golden_path = GOLDEN_DIR / f"{scenario_id}.json"
    if not golden_path.exists():
        raise SystemExit(f"No golden for '{scenario_id}' at {golden_path}")
    current_path = _find_current(scenario_id)

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    current = json.loads(current_path.read_text(encoding="utf-8"))

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
