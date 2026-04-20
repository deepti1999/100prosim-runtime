#!/usr/bin/env python3
"""PostToolUse hook: py_compile any .py file just written / edited.

Reads Claude Code tool event JSON on stdin. Exits 0 on success or skip,
prints JSON with systemMessage + exits 2 on syntax error (non-blocking
for PostToolUse — shown to the model so it can self-correct).
"""
import json
import os
import subprocess
import sys


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    f = (event.get("tool_input", {}).get("file_path")
         or event.get("tool_response", {}).get("filePath")
         or "")
    if not f.endswith(".py") or not os.path.exists(f):
        return 0

    skip_prefixes = (".venv/", "venv/", "staticfiles/")
    rel = f.replace("\\", "/")
    if any(p in rel for p in skip_prefixes):
        return 0

    r = subprocess.run(
        [sys.executable, "-m", "py_compile", f],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        return 0

    print(json.dumps({
        "systemMessage": f"py_compile FAILED for {f}\n" + r.stderr.strip()
    }))
    return 2


if __name__ == "__main__":
    sys.exit(main())
