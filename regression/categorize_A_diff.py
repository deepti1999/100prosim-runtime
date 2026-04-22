#!/usr/bin/env python3
"""Categorize every mismatch from `compare.py A-baseline-readonly` into
one of:

  1. Phase 2-A title/heading drift — intentional, per PDF §2.5.1.
  2. Phase 2-C number format drift — intentional, per PDF §2.5.2.
  3. Workspace-scoping value drift — pre-existing, unrelated to this push.
  4. Shape drift — probe keys removed/added because the page is now
     structured slightly differently.
  5. Other — meta fields (captured_on, note).

Gives a summary count at the bottom.
"""
import re
import subprocess
import sys
from pathlib import Path


def run_compare():
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["python", "regression/compare.py", "A-baseline-readonly"],
        capture_output=True, text=True, cwd=str(root),
    )
    return result.stdout + result.stderr


def main():
    text = run_compare()
    # Each mismatch block: key on indent-2, golden on indent-4, current on indent-4.
    # Pattern tolerates missing values ("<missing>") and mixed quoting styles.
    entries = []
    # Split by double-newline into per-mismatch chunks, then parse.
    for block in re.split(r"\n(?=  [^\s])", text):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        key_m = re.match(r"^  ([^\s].*)$", lines[0])
        if not key_m:
            continue
        key = key_m.group(1).strip()
        g = c = None
        for l in lines:
            if "golden  =" in l:
                g = l.split("=", 1)[1].strip()
            elif "current =" in l:
                c = l.split("=", 1)[1].strip()
        if g is None or c is None:
            continue
        entries.append((key, g, c))

    def _strip_quotes(s):
        s = s.strip()
        if len(s) >= 2 and s[0] in "'\"" and s[-1] in "'\"":
            s = s[1:-1]
        return s

    def _strip_seps(s):
        return re.sub(r"[,.]", "", s)

    n_title = n_numfmt = n_shape = n_workspace = n_meta = n_other = 0
    examples = {"title": [], "numfmt": [], "shape": [], "workspace": [], "meta": [], "other": []}

    for key, g, c in entries:
        g_u = _strip_quotes(g)
        c_u = _strip_quotes(c)

        if "_meta.captured_on" in key or "_meta.note" in key:
            n_meta += 1
            if len(examples["meta"]) < 2:
                examples["meta"].append((key, g_u, c_u))
            continue

        # Both are pure-number strings?
        is_num = lambda s: bool(re.fullmatch(r"[\d.,\-]+", s.strip()))
        if is_num(g_u) and is_num(c_u) and _strip_seps(g_u) == _strip_seps(c_u):
            n_numfmt += 1
            if len(examples["numfmt"]) < 3:
                examples["numfmt"].append((key, g_u, c_u))
            continue

        if "title" in key.lower() or ".h1" in key:
            n_title += 1
            if len(examples["title"]) < 3:
                examples["title"].append((key, g_u, c_u))
            continue

        if g_u == "<missing>" or c_u == "<missing>":
            n_shape += 1
            if len(examples["shape"]) < 3:
                examples["shape"].append((key, g_u, c_u))
            continue

        if is_num(g_u) and is_num(c_u):
            # Different numeric values — likely workspace-scope drift.
            n_workspace += 1
            if len(examples["workspace"]) < 3:
                examples["workspace"].append((key, g_u, c_u))
            continue

        n_other += 1
        if len(examples["other"]) < 3:
            examples["other"].append((key, g_u, c_u))

    total = len(entries)
    print(f"Total mismatches: {total}")
    print(f"  1. Phase 2-A title/heading drift (intentional): {n_title}")
    print(f"  2. Phase 2-C number format drift (intentional): {n_numfmt}")
    print(f"  3. Workspace-scoping value drift (pre-existing): {n_workspace}")
    print(f"  4. Shape drift (new/removed probes):            {n_shape}")
    print(f"  5. Meta (captured_on, note):                    {n_meta}")
    print(f"  6. Other:                                       {n_other}")
    print()
    for label, samples in examples.items():
        if not samples:
            continue
        print(f"Examples — {label}:")
        for k, g, c in samples:
            print(f"  {k}")
            print(f"    golden={g!r}")
            print(f"    current={c!r}")


if __name__ == "__main__":
    main()
