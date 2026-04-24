#!/usr/bin/env python3
"""Acid-test bench (T6) — wall-clock measurement of A/C/D user flows.

Replaces the earlier ``scripts/bench_acid_test.sh`` stub (which always
emitted ``elapsed_seconds: null, status: stub``). This script actually
drives the user flows over HTTP and records ``time.perf_counter()``
deltas.

Scenarios (from ``regression/playbook.md``):

A — read-only nav: login → /cockpit/, /landuse/, /renewable/,
    /verbrauch/, /bilanz/, /annual-electricity/. Pure GETs.

C — WS balance: login → POST /api/ws/apply-balance/ (solar) → poll
    /api/ws/balance-job/<id>/ until succeeded → record speicherdrift.

D — write flow: login → POST /api/save-verbrauch-user-input/ +
    /api/save-recalc-verbrauch/ → poll multi-pass recalc job →
    record annual_electricity_gwh.

Usage:

    python scripts/bench_acid_test.py [--scenario A|C|D|all] \
        [--runs N] [--user USERNAME] [--base-url URL]

Exit 0 on success. Emits JSON to stdout. Also writes a markdown
summary to verification/final_audit/bench_acid_test_<date>.md.

Pre-flight: /healthz + /readyz must return HTTP 200, else exit 1.

Caveats:
- Per-run resets the testsim workspace via the Django shell snippet
  for D scenario only (A and C are non-mutating). Reset is a no-op if
  the workspace is already at baseline.
- POST endpoints take CSRF tokens; the script extracts them from the
  GET /login/ response and re-fetches /simulation/ to refresh after
  login.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import urllib.parse
from datetime import date, datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener


REPO = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_USER = "testsim"
DEFAULT_PASS = "TestSim!2026"
POLL_INTERVAL_S = 0.5
POLL_TIMEOUT_S = 240


def _commit_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return "unknown"


def _login(base_url: str, user: str, password: str):
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    resp = opener.open(base_url + "/login/")
    html = resp.read().decode("utf-8", errors="ignore")
    m = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
    if not m:
        raise RuntimeError("CSRF token not found on /login/")
    csrf = m.group(1)
    data = urllib.parse.urlencode({
        "username": user,
        "password": password,
        "csrfmiddlewaretoken": csrf,
    }).encode("utf-8")
    req = Request(
        base_url + "/login/",
        data=data,
        headers={
            "Referer": base_url + "/login/",
            "X-CSRFToken": csrf,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    opener.open(req)
    opener.open(base_url + "/simulation/")
    new_csrf = csrf
    for c in cj:
        if c.name == "csrftoken":
            new_csrf = c.value
            break
    return opener, new_csrf


def _post_json(opener, base_url, path, csrf, body=None):
    raw = json.dumps(body or {}).encode("utf-8")
    req = Request(
        base_url + path,
        data=raw,
        headers={
            "Referer": base_url + "/",
            "X-CSRFToken": csrf,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    body_text = opener.open(req).read().decode("utf-8", errors="ignore")
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return {"_raw": body_text}


def _get(opener, base_url, path):
    return opener.open(base_url + path).read()


def _get_json(opener, base_url, path):
    return json.loads(_get(opener, base_url, path))


def _wait_for_balance_job(opener, base_url, job_id):
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        s = _get_json(opener, base_url, f"/api/ws/balance-job/{job_id}/")
        if s.get("status") == "succeeded":
            return s
        if s.get("status") in ("failed", "cancelled"):
            raise RuntimeError(f"job {job_id} ended {s.get('status')}: {s.get('error')!r}")
        time.sleep(POLL_INTERVAL_S)
    raise RuntimeError(f"job {job_id} did not succeed within {POLL_TIMEOUT_S}s")


def _preflight(base_url: str) -> None:
    for path, label in (("/healthz", "healthz"), ("/readyz", "readyz")):
        try:
            opener = build_opener()
            r = opener.open(base_url + path)
            if r.status != 200:
                raise SystemExit(
                    f"PREFLIGHT FAIL: {label} returned HTTP {r.status} "
                    f"at {base_url+path}"
                )
        except (HTTPError, URLError) as e:
            raise SystemExit(
                f"PREFLIGHT FAIL: cannot reach {base_url+path}: {e}"
            )


def _scenario_A(opener, base_url, csrf) -> Dict[str, Any]:
    """Read-only nav over 6 pages."""
    pages = [
        "/cockpit/", "/landuse/", "/renewable/",
        "/verbrauch/", "/bilanz/", "/annual-electricity/",
    ]
    sizes = []
    for path in pages:
        body = _get(opener, base_url, path)
        sizes.append(len(body))
    return {
        "pages_visited": len(pages),
        "total_bytes_read": sum(sizes),
    }


def _scenario_C(opener, base_url, csrf) -> Dict[str, Any]:
    """WS solar balance trigger + poll."""
    resp = _post_json(opener, base_url, "/api/ws/apply-balance/", csrf, {})
    job_id = resp.get("job_id")
    if not job_id:
        if resp.get("success") and not resp.get("queued"):
            return {"job_status": "succeeded", "queued": False}
        raise RuntimeError(f"apply-balance trigger failed: {resp!r}")
    final = _wait_for_balance_job(opener, base_url, job_id)
    summary = _get_json(opener, base_url, "/api/ws/summary/")
    cur = summary.get("current") or {}
    return {
        "job_status": final.get("status"),
        "speicherdrift_gwh": cur.get("storage_drift"),
        "iterations": (summary.get("goal_seek") or {}).get("iterations"),
    }


def _scenario_D(opener, base_url, csrf) -> Dict[str, Any]:
    """Write flow: edit verbrauch 1.1.2 (95→100) + multi-pass recalc."""
    save = _post_json(
        opener, base_url, "/api/save-verbrauch-user-input/", csrf,
        {"code": "1.1.2", "user_percent": 100},
    )
    if not save.get("success"):
        raise RuntimeError(f"save 1.1.2 failed: {save!r}")
    recalc = _post_json(opener, base_url, "/api/save-recalc-verbrauch/", csrf, {})
    job_id = recalc.get("job_id") if recalc.get("queued") else None
    if job_id:
        final = _wait_for_balance_job(opener, base_url, job_id)
        recalc_status = final.get("status")
    else:
        recalc_status = recalc.get("status", "unknown")
    summary = _get_json(opener, base_url, "/api/ws/summary/")
    return {
        "save_status": save.get("success"),
        "recalc_status": recalc_status,
        "annual_electricity_gwh": (
            (summary.get("goal_seek") or {}).get("annual_electricity")
        ),
    }


def _reset_testsim_workspace_in_container() -> Optional[str]:
    """Best-effort reset via docker compose exec — returns error string
    on failure so the caller can document the caveat."""
    snippet = (
        "from django.contrib.auth import get_user_model\n"
        "from simulator.models import LandUse, VerbrauchData, RenewableData, BalanceJob\n"
        "from simulator.ws_models import WSData\n"
        "from simulator.workspace_service import ensure_user_workspace_data\n"
        "u = get_user_model().objects.get(username='testsim')\n"
        "BalanceJob.objects.filter(created_by=u).delete()\n"
        "for M in (LandUse, VerbrauchData, RenewableData, WSData):\n"
        "    M.all_objects.filter(owner=u).delete()\n"
        "ensure_user_workspace_data(u)\n"
        "print('reset OK')\n"
    )
    try:
        r = subprocess.run(
            ["docker", "compose", "exec", "-T", "web",
             "python", "manage.py", "shell", "-c", snippet],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return f"reset failed (exit {r.returncode}): {r.stderr.strip()[:200]}"
    except Exception as e:  # noqa: BLE001
        return f"reset exception: {type(e).__name__}: {e}"
    return None


SCENARIO_FNS = {
    "A": (_scenario_A, "read-only nav (6 pages)", False),
    "C": (_scenario_C, "WS solar balance trigger+poll", False),
    "D": (_scenario_D, "verbrauch edit + multi-pass recalc", True),
}


def _percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = max(0, min(len(sorted_vals) - 1, int(round(p * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


def run_scenario(name: str, base_url: str, user: str, password: str,
                 runs: int) -> Dict[str, Any]:
    fn, description, mutates = SCENARIO_FNS[name]
    runs_data: List[float] = []
    end_states: List[Dict[str, Any]] = []
    reset_caveats: List[str] = []
    last_error: Optional[str] = None

    for i in range(runs):
        if mutates:
            err = _reset_testsim_workspace_in_container()
            if err:
                reset_caveats.append(f"run {i+1}: {err}")
        try:
            opener, csrf = _login(base_url, user, password)
            t0 = time.perf_counter()
            end_state = fn(opener, base_url, csrf)
            elapsed = time.perf_counter() - t0
            runs_data.append(elapsed)
            end_states.append(end_state)
        except Exception as e:  # noqa: BLE001
            last_error = f"run {i+1}: {type(e).__name__}: {e}"
            break

    if not runs_data:
        return {
            "scenario": name,
            "description": description,
            "status": "failed",
            "error": last_error or "no runs completed",
            "elapsed_seconds": None,
        }

    sorted_runs = sorted(runs_data)
    median = statistics.median(sorted_runs)
    return {
        "scenario": name,
        "description": description,
        "runs": runs,
        "completed": len(runs_data),
        "elapsed_seconds": round(median, 4),  # back-compat alias for median
        "elapsed_seconds_median": round(median, 4),
        "elapsed_seconds_p95": round(_percentile(sorted_runs, 0.95), 4),
        "elapsed_seconds_min": round(min(sorted_runs), 4),
        "elapsed_seconds_max": round(max(sorted_runs), 4),
        "elapsed_seconds_each": [round(x, 4) for x in runs_data],
        "end_state_sample": end_states[0],
        "reset_caveats": reset_caveats,
        "status": "completed",
    }


def emit_markdown(payload: Dict[str, Any]) -> Path:
    out_dir = REPO / "verification" / "final_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"bench_acid_test_{date.today()}.md"
    lines = [
        f"# Acid-test bench — {payload['timestamp']}",
        "",
        f"- base_url: `{payload['base_url']}`",
        f"- commit_sha: `{payload['commit_sha']}`",
        f"- user: `{payload['user']}`",
        f"- runs per scenario: {payload['runs']}",
        f"- overall status: **{payload['status']}**",
        "",
        "| Scenario | Description | Runs | Median (s) | p95 (s) | Min (s) | Max (s) | Status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for sc in payload["scenarios"]:
        if sc["status"] == "completed":
            lines.append(
                f"| {sc['scenario']} | {sc['description']} | {sc['completed']}"
                f" | {sc['elapsed_seconds_median']} | {sc['elapsed_seconds_p95']}"
                f" | {sc['elapsed_seconds_min']} | {sc['elapsed_seconds_max']}"
                f" | ✅ |"
            )
        else:
            lines.append(
                f"| {sc['scenario']} | {sc['description']} | 0"
                f" | — | — | — | — | ❌ {sc.get('error', '?')[:60]} |"
            )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="T6 acid-test bench")
    p.add_argument("--scenario", choices=("A", "C", "D", "all"), default="all")
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--user", default=os.environ.get("BENCH_USER", DEFAULT_USER))
    p.add_argument("--base-url", default=os.environ.get("BENCH_BASE_URL", DEFAULT_BASE_URL))
    args = p.parse_args(argv)

    base_url = args.base_url.rstrip("/")
    password = os.environ.get("BENCH_PASS", DEFAULT_PASS)

    _preflight(base_url)

    scenarios = ["A", "C", "D"] if args.scenario == "all" else [args.scenario]
    results = []
    for name in scenarios:
        res = run_scenario(name, base_url, args.user, password, args.runs)
        results.append(res)

    overall_status = (
        "completed" if all(r["status"] == "completed" for r in results) else "failed"
    )

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "commit_sha": _commit_sha(),
        "user": args.user,
        "runs": args.runs,
        "scenarios": results,
        "status": overall_status,
        # Back-compat: top-level elapsed_seconds reflects the first scenario's
        # median — earlier .sh stub callers expect a single elapsed_seconds
        # field at the top level.
        "elapsed_seconds": results[0].get("elapsed_seconds") if results else None,
    }

    md_path = emit_markdown(payload)
    payload["markdown_summary_path"] = str(md_path.relative_to(REPO))

    print(json.dumps(payload, indent=2, default=str))
    return 0 if overall_status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
