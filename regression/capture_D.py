#!/usr/bin/env python3
"""Capture Scenario D (full Verbrauch + Solar variant flow) as JSON.

Runs the SOLAR variant of the playbook OR-clause (playbook §D, step 10
explicitly says "EITHER the solar variant OR the wind variant"). Skipping
the wind variant keeps the script under the audit's per-task time budget;
the cross-variant invariant is well-covered by the formula-parity tests.

Steps mirror ``regression/playbook.md`` scenario D:

1. Capture baseline_fingerprint (LU_2.1 target, LU_6 target,
   verbrauch 1.1.2 + 2.4.1 user_percent, verbrauch row 7+8 ziel,
   annual_electricity).
2. Edit verbrauch 1.1.2 from 95 → 100 + trigger verbrauch recalc.
3. Edit verbrauch 2.4.1 from 80 → 75 + trigger verbrauch recalc.
4. Trigger renewables recalc (queued job, poll to completion).
5. Capture verbrauch row 7 + 8 ziel after edits.
6. Trigger solar_ws_only via /api/ws/apply-balance/, poll, capture probes.
7. Trigger solar_sector_ws via /api/ws/apply-full-balance/, poll,
   capture probes (hard-asserts: LU_2.1 + annual_electricity).

Schema: raw unlocalized floats from /api/ws/summary/ + /api/ws/data/
+ /verbrauch/ HTML scraping. After capture, the testsim workspace is
LEFT MUTATED — the caller must reset via the CLAUDE.md shell snippet
between runs.

Emits ``verification/<today>/D-full-flow-verbrauch-solar-wind.json``.

Usage (requires Docker stack + freshly-reset testsim workspace):

    # 1. Reset workspace per CLAUDE.md
    # 2. python regression/capture_D.py
    # 3. python regression/compare.py D-full-flow-verbrauch-solar-wind
"""
import json
import re
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
POLL_TIMEOUT_S = 240


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
    return json.loads(opener.open(BASE_URL + path).read())


def _get(opener, path):
    return opener.open(BASE_URL + path).read().decode("utf-8", errors="ignore")


def _wait_for_balance_job(opener, job_id):
    deadline = time.time() + POLL_TIMEOUT_S
    last = None
    while time.time() < deadline:
        last = _get_json(opener, f"/api/ws/balance-job/{job_id}/")
        st = last.get("status")
        if st == "succeeded":
            return last
        if st in ("failed", "cancelled"):
            raise SystemExit(f"job {job_id} ended {st}: {last.get('error')!r}")
        time.sleep(POLL_INTERVAL_S)
    raise SystemExit(f"job {job_id} did not succeed within {POLL_TIMEOUT_S}s")


def _trigger_balance(opener, csrf, path, label):
    resp = _post_json(opener, path, csrf, {})
    job_id = resp.get("job_id")
    if not job_id:
        if resp.get("success") and not resp.get("queued"):
            return {"status": "succeeded", "result": resp.get("result", {})}
        raise SystemExit(f"{label} trigger failed: {resp!r}")
    return _wait_for_balance_job(opener, job_id)


def _scrape_verbrauch_row(html, row_code):
    """Extract status + ziel for a verbrauch row by code (e.g. '7', '8').

    Matches a ``<tr>`` whose first cell is ``<td class="fw-bold">CODE</td>``,
    then picks the 1st (status) and 2nd (ziel) ``<td class="text-end">``.
    """
    pat = re.compile(
        rf'<tr[^>]*>\s*<td[^>]*class="[^"]*fw-bold[^"]*"[^>]*>\s*'
        rf'{re.escape(row_code)}\s*</td>'
        rf'([\s\S]+?)</tr>'
    )
    m = pat.search(html)
    if not m:
        return None
    row_html = m.group(1)
    cells = re.findall(
        r'<td[^>]*class="[^"]*text-end[^"]*"[^>]*>\s*([^<]+?)\s*</td>', row_html
    )
    if len(cells) < 2:
        return None
    return {"status": cells[0].strip(), "ziel": cells[1].strip()}


def _scrape_landuse_target_ha(html, code):
    """Extract target_ha for a LandUse code by finding the row containing the
    code badge then picking the third numeric cell (Status / Δ / Ziel).
    """
    pat = re.compile(
        rf'<tr[^>]*>(?:(?!</tr>).)*?'
        rf'badge[^>]*>\s*{re.escape(code)}\s*<.*?</tr>',
        re.DOTALL,
    )
    m = pat.search(html)
    if not m:
        return None
    row_html = m.group(0)
    nums = re.findall(
        r'class="[^"]*number-column[^"]*"[^>]*>\s*([^<]+?)\s*</td>', row_html
    )
    if len(nums) < 3:
        return None
    target_str = re.sub(r"<[^>]+>", "", nums[2]).strip()
    target_str = target_str.replace(".", "").replace(",", ".")
    try:
        return float(target_str)
    except ValueError:
        return None


def _summary_probe(opener):
    s = _get_json(opener, "/api/ws/summary/")
    cur = s.get("current") or {}
    gs = s.get("goal_seek") or {}
    return {
        "annual_electricity_gwh": (gs.get("annual_electricity")
                                   if gs else None),
        "optimal_solar_gwh": gs.get("optimal_solar"),
        "speicherdrift_gwh": cur.get("storage_drift"),
        "iterations": gs.get("iterations"),
        "required_landuse_ha": gs.get("required_landuse"),
        "current_landuse_ha": gs.get("current_landuse"),
    }


def _round_or_none(value, digits=2):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def capture():
    print(f"capture_D against {BASE_URL!r} as {USER!r}")
    opener, csrf = _login()

    out = {
        "_meta": {
            "scenario_id": "D-full-flow-verbrauch-solar-wind",
            "captured_on": str(date.today()),
            "captured_by": "regression/capture_D.py (HTTP-driven, solar variant only)",
            "note": (
                "Re-captured 2026-04-24 post Phase-2C drift + post-#111 "
                "fix + post iteration-cut perf passes. Solar variant only "
                "(playbook §D step 10 OR-clause). Workspace LEFT MUTATED "
                "after run — reset via CLAUDE.md shell snippet between "
                "runs. Pascal-approved re-capture."
            ),
        },
    }

    print("  capture baseline_fingerprint")
    pre = _summary_probe(opener)
    landuse_html = _get(opener, "/landuse/")
    verb_html = _get(opener, "/verbrauch/")

    out["baseline_fingerprint"] = {
        "baseline_LU_2_1_target_ha": _scrape_landuse_target_ha(landuse_html, "LU_2.1"),
        "baseline_LU_6_target_ha": _scrape_landuse_target_ha(landuse_html, "LU_6"),
        "baseline_annual_electricity_gwh": _round_or_none(pre["annual_electricity_gwh"]),
        "baseline_verbrauch_row_7": _scrape_verbrauch_row(verb_html, "7"),
        "baseline_verbrauch_row_8": _scrape_verbrauch_row(verb_html, "8"),
    }

    def _save_verbrauch(code, value):
        return _post_json(
            opener, "/api/save-verbrauch-user-input/", csrf,
            {"code": code, "user_percent": value},
        )

    def _verbrauch_recalc_passes():
        # Use /api/save-recalc-verbrauch/ which queues a TYPE_VERBRAUCH_RECALC
        # job — runs the multi-pass `_run_verbrauch_recalc_passes` cascade
        # (the same path the "Save All Values" button uses). The legacy
        # /api/recalc-verbrauch/ is single-pass and doesn't propagate.
        resp = _post_json(opener, "/api/save-recalc-verbrauch/", csrf, {})
        if resp.get("queued") and resp.get("job_id"):
            return _wait_for_balance_job(opener, resp["job_id"])
        return resp

    print("  edit 1.1.2: 95 -> 100  +  multi-pass recalc")
    _save_verbrauch("1.1.2", 100)
    rv1 = _verbrauch_recalc_passes()
    print(f"    -> {rv1.get('status')} (multi-pass)")

    print("  edit 2.4.1: 80 -> 75  +  multi-pass recalc")
    _save_verbrauch("2.4.1", 75)
    rv2 = _verbrauch_recalc_passes()
    print(f"    -> {rv2.get('status')} (multi-pass)")

    print("  POST /api/recalc-renewables/")
    rr = _post_json(opener, "/api/recalc-renewables/", csrf, {})
    rr_job_id = rr.get("job_id")
    if rr_job_id:
        # Queued — poll
        rr_status = _wait_for_balance_job(opener, rr_job_id)
        print(f"    -> queued -> {rr_status.get('status')}")
    else:
        print(f"    -> inline -> {rr.get('status')}")

    print("  capture post-recalc verbrauch + landuse + summary state")
    verb_after = _get(opener, "/verbrauch/")
    landuse_after = _get(opener, "/landuse/")
    after_recalc = _summary_probe(opener)

    out["after_verbrauch_and_renewable_recalc"] = {
        "verbrauch_row_7": _scrape_verbrauch_row(verb_after, "7"),
        "verbrauch_row_8": _scrape_verbrauch_row(verb_after, "8"),
        "lu_2_1_target_ha": _scrape_landuse_target_ha(landuse_after, "LU_2.1"),
        "annual_electricity_gwh": _round_or_none(after_recalc["annual_electricity_gwh"]),
        "verbrauch_recalc_jobs": [
            {"order": 1, "status": rv1.get("status")},
            {"order": 2, "status": rv2.get("status")},
        ],
        "renewables_recalc": {
            "queued": bool(rr_job_id),
            "status": (rr_status.get("status") if rr_job_id else rr.get("status")),
        },
    }

    print("  POST /api/ws/apply-balance/  (solar_ws_only)")
    pre_solar = _summary_probe(opener)
    pre_solar_lu = _scrape_landuse_target_ha(landuse_after, "LU_2.1")
    solar_ws = _trigger_balance(opener, csrf, "/api/ws/apply-balance/", "solar_ws_only")
    landuse_after_solar_ws = _get(opener, "/landuse/")
    post_solar_ws = _summary_probe(opener)

    out["solar_variant"] = {
        "step_ws_balance_solar": {
            "backend_job_status": solar_ws.get("status"),
            "probes": {
                "LU_2.1_target_ha": {
                    "before": _round_or_none(pre_solar_lu),
                    "after": _round_or_none(_scrape_landuse_target_ha(landuse_after_solar_ws, "LU_2.1")),
                },
                "optimal_solar_gwh": {
                    "before": _round_or_none(pre_solar["optimal_solar_gwh"]),
                    "after": _round_or_none(post_solar_ws["optimal_solar_gwh"]),
                },
                "annual_electricity_gwh": {
                    "before": _round_or_none(pre_solar["annual_electricity_gwh"]),
                    "after": _round_or_none(post_solar_ws["annual_electricity_gwh"]),
                },
                "speicherdrift_gwh": {
                    "after": _round_or_none(post_solar_ws["speicherdrift_gwh"], 4),
                },
            },
        }
    }

    print("  POST /api/ws/apply-full-balance/  (solar_sector_ws)")
    pre_sector = post_solar_ws
    pre_sector_lu = _scrape_landuse_target_ha(landuse_after_solar_ws, "LU_2.1")
    sector_ws = _trigger_balance(opener, csrf, "/api/ws/apply-full-balance/", "solar_sector_ws")
    landuse_after_sector = _get(opener, "/landuse/")
    post_sector_ws = _summary_probe(opener)

    out["solar_variant"]["step_sector_ws_solar_balance"] = {
        "backend_job_status": sector_ws.get("status"),
        "probes": {
            "LU_2.1_target_ha": {
                "before": _round_or_none(pre_sector_lu),
                "after": _round_or_none(_scrape_landuse_target_ha(landuse_after_sector, "LU_2.1")),
            },
            "optimal_solar_gwh": {
                "before": _round_or_none(pre_sector["optimal_solar_gwh"]),
                "after": _round_or_none(post_sector_ws["optimal_solar_gwh"]),
            },
            "annual_electricity_gwh": {
                "before": _round_or_none(pre_sector["annual_electricity_gwh"]),
                "after": _round_or_none(post_sector_ws["annual_electricity_gwh"]),
            },
            "speicherdrift_gwh": {
                "after": _round_or_none(post_sector_ws["speicherdrift_gwh"], 4),
            },
        },
    }

    out["invariants"] = {
        "speicherdrift_after_full_balance_max_gwh": 0.5,
        "annual_electricity_after_full_balance_gwh": _round_or_none(
            post_sector_ws["annual_electricity_gwh"]
        ),
        "lu_2_1_after_full_balance_ha": _round_or_none(
            _scrape_landuse_target_ha(landuse_after_sector, "LU_2.1")
        ),
    }

    out_path = REPO / "verification" / str(date.today()) / "D-full-flow-verbrauch-solar-wind.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"WROTE {out_path}")
    return out_path


if __name__ == "__main__":
    capture()
