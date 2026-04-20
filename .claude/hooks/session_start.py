#!/usr/bin/env python3
"""SessionStart hook: inject stack state as additionalContext so Claude sees it up front."""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    lines = ["## Stack state (from SessionStart hook)"]

    # docker compose ps
    try:
        r = subprocess.run(
            ["docker", "compose", "ps", "--format", "{{.Service}}:{{.Status}}"],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        ps_out = (r.stdout or "").strip() or "(no services running)"
        lines.append("```\n" + ps_out + "\n```")
    except Exception as exc:
        lines.append(f"(docker ps failed: {exc})")

    # git branch + dirty state
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO, capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "(none)"
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO, capture_output=True, text=True, timeout=5,
        ).stdout.strip().splitlines()
        lines.append(f"git: branch={branch}  uncommitted={len(status)}")
    except Exception as exc:
        lines.append(f"(git status failed: {exc})")

    ctx = "\n".join(lines)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": ctx,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
