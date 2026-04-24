#!/usr/bin/env python3
"""Capture Scenario C (WS Solar + Wind balance) current state as JSON.

Drives the C scenario via HTTP — POSTs the WS-only solar + wind balance
queue endpoints, polls each job to completion, then reads:

- ``/api/ws/summary/`` → ``current.{ueberschuss,einspeich,ausspeich,
  abregelung}_sum`` summary-card values + ``goal_seek.*`` (optimal_solar,
  storage_drift, annual_electricity, iterations, required_landuse) +
  ``goal_seek_wind.*`` (mirror for wind).
- ``/annual-electricity/`` HTML → scrapes the inline
  ``const vals = { ... };`` block (already ``|unlocalize``-d per the
  template, so values are JS parseFloat-clean raw floats).

Emits ``verification/<today>/C-ws-balance.json`` so
``python regression/compare.py C-ws-balance`` can diff against
``regression/golden/C-ws-balance.json``.

Why HTTP not Playwright: the WS summary endpoint exposes everything the
``/ws/`` page would otherwise show via JS, and the annual-electricity
SVG values are server-rendered into ``vals = {...}`` (post-#111 fix
pattern). Captures cleanly without a browser.

Usage (requires Docker stack running + testsim user):

    python regression/capture_C.py
    python regression/compare.py C-ws-balance
"""
import json
import re
import sys
import time
import urllib.parse
from datetime import date
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener

REPO = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8001"
USER = "testsim"
PASS = "TestSim!2026"
POLL_INTERVAL_S = 1.0
POLL_TIMEOUT_S = 180


def _login():
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    resp = opener.open(BASE_URL + "/login/")
    html = resp.read().decode("utf-8", errors="ignore")
    m = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
    if not m:
        raise SystemExit("Could not find CSRF token on /login/")
    csrf = m.group(1)
    data = urllib.parse.urlencode({
        "username": USER,
        "password": PASS,
        "csrfmiddlewaretoken": csrf,
    }).encode("utf-8")
    req = Request(
        BASE_URL + "/login/",
        data=data,
        headers={
            "Referer": BASE_URL + "/login/",
            "X-CSRFToken": csrf,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    opener.open(req)
    # Re-fetch a page to refresh CSRF for subsequent JSON POSTs.
    opener.open(BASE_URL + "/simulation/")
    new_csrf = None
    for c in cj:
        if c.name == "csrftoken":
            new_csrf = c.value
            break
    return opener, (new_csrf or csrf)


def _post_json(opener, path, csrf, body=None):
    raw = json.dumps(body or {}).encode("utf-8")
    req = Request(
        BASE_URL + path,
        data=raw,
        headers={
            "Referer": BASE_URL + "/",
            "X-CSRFToken": csrf,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    resp = opener.open(req)
    body = resp.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body, "_status": resp.status}


def _get_json(opener, path):
    resp = opener.open(BASE_URL + path)
    return json.loads(resp.read())


def _get(opener, path):
    return opener.open(BASE_URL + path).read().decode("utf-8", errors="ignore")


def _trigger_balance_and_wait(opener, csrf, kind):
    """POST a WS balance trigger and poll its BalanceJob until succeeded."""
    if kind == "solar":
        path = "/api/ws/apply-balance/"
        expected_job_type = "solar_ws_only"
    else:
        path = "/api/ws/apply-balance-wind/"
        expected_job_type = "wind_ws_only"
    resp = _post_json(opener, path, csrf, {})
    job_id = resp.get("job_id")
    if not job_id:
        if resp.get("success") and not resp.get("queued"):
            return {"status": "succeeded", "result": resp.get("result", {})}, expected_job_type
        raise SystemExit(f"{kind} balance trigger failed: {resp!r}")
    deadline = time.time() + POLL_TIMEOUT_S
    last = None
    while time.time() < deadline:
        last = _get_json(opener, f"/api/ws/balance-job/{job_id}/")
        if last.get("status") == "succeeded":
            return last, expected_job_type
        if last.get("status") in ("failed", "cancelled"):
            raise SystemExit(
                f"{kind} job {job_id} ended {last.get('status')}: "
                f"{last.get('error', '')!r}"
            )
        time.sleep(POLL_INTERVAL_S)
    raise SystemExit(
        f"{kind} job {job_id} did not succeed within {POLL_TIMEOUT_S}s "
        f"(last status: {last!r})"
    )


def _scrape_vals_from_annual_electricity(html):
    """Extract ``const vals = { key: float, ... };`` from inline JS."""
    m = re.search(r'const vals\s*=\s*\{([\s\S]+?)\};', html)
    if not m:
        raise SystemExit("Could not find `const vals = ...` in /annual-electricity/")
    body = m.group(1)
    out = {}
    for kv in re.finditer(r'^\s*(\w+)\s*:\s*([-+0-9.eE]+)\s*[,}]', body, re.MULTILINE):
        key = kv.group(1)
        try:
            out[key] = float(kv.group(2))
        except ValueError:
            continue
    return out


def _round_float(value, digits=2):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def capture():
    print(f"capture_C against {BASE_URL!r} as {USER!r}")
    opener, csrf = _login()

    # Note: skip POST /api/baseline/create/ — that endpoint is staff-only
    # (creates the SHARED admin baseline). testsim is a regular user; the
    # workspace was already reset before this script via the CLAUDE.md shell
    # snippet. The C scenario's balance is a no-op on the balanced seed,
    # so post-state == pre-state and no restore is needed.

    out = {
        "_meta": {
            "scenario_id": "C-ws-balance",
            "captured_on": str(date.today()),
            "captured_by": "regression/capture_C.py (HTTP-driven)",
            "note": (
                "Re-captured post Phase-2C drift + post-#111 fix. "
                "Schema: raw unlocalized floats from /api/ws/summary/ + "
                "annual-electricity inline `vals` JS object. "
                "Hard invariant: speicherdrift_*_gwh ~= 0 after balance "
                "on the balanced seed. Pascal-approved re-capture."
            ),
        },
    }

    print("  POST /api/ws/apply-balance/   (Solar)")
    solar_status, solar_jt = _trigger_balance_and_wait(opener, csrf, "solar")
    print(f"    solar job: {solar_jt} -> {solar_status.get('status')}")

    print("  POST /api/ws/apply-balance-wind/  (Wind)")
    wind_status, wind_jt = _trigger_balance_and_wait(opener, csrf, "wind")
    print(f"    wind  job: {wind_jt} -> {wind_status.get('status')}")

    print("  GET  /api/ws/summary/   (current cards + goal_seek state)")
    summary = _get_json(opener, "/api/ws/summary/")
    cur = summary.get("current") or {}
    gs = summary.get("goal_seek") or {}
    gsw = summary.get("goal_seek_wind") or {}

    out["invariants"] = {
        "speicherdrift_solar_gwh": _round_float(gs.get("storage_drift"), 4),
        "speicherdrift_wind_gwh": _round_float(gsw.get("storage_drift"), 4),
    }

    out["balance_jobs"] = {
        "solar": {"job_type": solar_jt, "status": solar_status.get("status")},
        "wind": {"job_type": wind_jt, "status": wind_status.get("status")},
    }

    out["ws_summary_cards"] = {
        "ueberschuss_sum_gwh": _round_float(cur.get("ueberschuss_sum")),
        "einspeich_sum_gwh": _round_float(cur.get("einspeich_sum")),
        "ausspeich_sum_gwh": _round_float(cur.get("ausspeich_sum")),
        "abregelung_sum_gwh": _round_float(cur.get("abregelung_sum")),
        "storage_drift_gwh": _round_float(cur.get("storage_drift"), 4),
    }

    out["goal_seek_solar"] = {
        "optimal_solar_gwh": _round_float(gs.get("optimal_solar")),
        "storage_drift_gwh": _round_float(gs.get("storage_drift"), 4),
        "annual_electricity_gwh": _round_float(gs.get("annual_electricity")),
        "iterations": gs.get("iterations"),
        "required_landuse_ha": _round_float(gs.get("required_landuse")),
        "current_landuse_ha": _round_float(gs.get("current_landuse")),
        "landuse_change_ha": _round_float(gs.get("landuse_change")),
    }

    out["goal_seek_wind"] = {
        "optimal_wind_gwh": _round_float(gsw.get("optimal_wind")),
        "storage_drift_gwh": _round_float(gsw.get("storage_drift"), 4),
        "annual_electricity_gwh": _round_float(gsw.get("annual_electricity")),
        "iterations": gsw.get("iterations"),
        "required_landuse_ha": _round_float(gsw.get("required_landuse")),
        "current_landuse_ha": _round_float(gsw.get("current_landuse")),
        "landuse_change_ha": _round_float(gsw.get("landuse_change")),
    }

    print("  GET  /annual-electricity/   (scrape inline `vals` JS object)")
    ae_html = _get(opener, "/annual-electricity/")
    ae_vals = _scrape_vals_from_annual_electricity(ae_html)
    out["annual_electricity_diagram"] = {
        k: _round_float(v) for k, v in sorted(ae_vals.items())
    }

    # Skip POST /api/baseline/restore/ — testsim has no admin baseline to
    # restore from in this minimal environment, and the C balance is a
    # no-op on the balanced seed.

    out_path = REPO / "verification" / str(date.today()) / "C-ws-balance.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"WROTE {out_path}")
    return out_path


if __name__ == "__main__":
    capture()
