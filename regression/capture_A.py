#!/usr/bin/env python3
"""Capture Scenario A (baseline-readonly) current state as JSON.

Reads the live pages via authenticated HTTP GET, extracts the exact
same probes the golden at ``regression/golden/A-baseline-readonly.json``
defines, and writes the current JSON to
``verification/<today>/A-baseline-readonly.json``. Then the caller can
``python regression/compare.py A-baseline-readonly`` to see the diff.

Usage (requires Docker stack running + testsim user):

    python regression/capture_A.py
    python regression/compare.py A-baseline-readonly
"""
import json
import re
import sys
import urllib.parse
from datetime import date
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener

REPO = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8001"
USER = "testsim"
PASS = "TestSim!2026"


def _login():
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    # GET /login/ to capture csrftoken
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
    return opener


def _get(opener, path):
    resp = opener.open(BASE_URL + path)
    return resp.read().decode("utf-8", errors="ignore")


# ---- Probe extractors ---------------------------------------------------
def _title(html):
    m = re.search(r"<title>([^<]+)</title>", html)
    return m.group(1).strip() if m else None


def _h1(html):
    m = re.search(r'<h1[^>]*class="h2"[^>]*>([^<]+)</h1>', html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", html)
    return m.group(1).strip() if m else None


def _dashboard_cards(html):
    # simulation page numeric counts next to the sector labels
    pairs = {}
    for key, label in [
        ("flaechennutzung_count", "Flächennutzung"),
        ("erneuerbare_count", "Erneuerbare Energien"),
        ("verbrauch_count", "Verbrauch"),
        ("szenario_abgleich_count", "Szenario-Abgleich"),
    ]:
        m = re.search(
            rf"{re.escape(label)}.*?<h3[^>]*>\s*([\d.,\-]+|--)\s*</h3>",
            html, re.DOTALL,
        )
        pairs[key] = m.group(1).strip() if m else None
    return pairs


def _landuse_rows(html):
    # Each row: td with badge code, td with bold name, number-column tds.
    rows = {}
    # Quick heuristic: iterate <tr> blocks inside the main table.
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL):
        m_code = re.search(r'class="badge bg-secondary">([^<]+)</span>', tr)
        if not m_code:
            continue
        code = m_code.group(1).strip()
        m_name = re.search(r"<strong>([^<]+)</strong>", tr)
        nums = re.findall(r'class="number-column[^"]*"[^>]*>\s*([^<]+?)\s*</td>', tr)
        if not nums:
            continue
        # Strip any trailing <strong>/<span> wrapping
        nums = [re.sub(r"<[^>]+>", "", n).strip() for n in nums]
        # Status (ha) is nums[0], Ziel (ha) is nums[2] in our current column order.
        status_ha = nums[0] if len(nums) > 0 else None
        target_ha = nums[2] if len(nums) > 2 else None
        rows[code] = {
            "name": m_name.group(1).strip() if m_name else None,
            "status_ha": status_ha,
            "target_ha": target_ha,
        }
    return rows


def _count_rows(html, pattern):
    return len(re.findall(pattern, html))


def _bilanz_headings(html):
    return [m.strip() for m in re.findall(r"<h3[^>]*>([^<]+)</h3>", html)]


def capture():
    opener = _login()

    out = {
        "_meta": {
            "scenario_id": "A-baseline-readonly",
            "captured_on": str(date.today()),
            "note": "Auto-captured by regression/capture_A.py. Run compare.py to diff.",
        },
        "pages": {},
    }

    # /simulation/
    html = _get(opener, "/simulation/")
    out["pages"]["/simulation/"] = {
        "title": _title(html),
        "h1": _h1(html),
        "dashboard_cards": _dashboard_cards(html),
    }

    # /landuse/
    html = _get(opener, "/landuse/")
    out["pages"]["/landuse/"] = {
        "title": _title(html),
        "h1": _h1(html),
        "row_count": _count_rows(html, r'class="badge bg-secondary">LU_'),
        "landuse": _landuse_rows(html),
    }

    # /renewable/, /verbrauch/, /annual-electricity/, /bilanz/, /cockpit/, /ws/
    # For these we only capture the cheap / shape-level probes. The deep
    # comparisons for these live in the dedicated test suites.
    for path in ["/renewable/", "/verbrauch/", "/annual-electricity/",
                 "/bilanz/", "/cockpit/", "/ws/"]:
        html = _get(opener, path)
        out["pages"][path] = {
            "title": _title(html),
            "h1": _h1(html),
        }

    out_path = REPO / "verification" / str(date.today()) / "A-baseline-readonly.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out_path}")
    return out_path


if __name__ == "__main__":
    capture()
