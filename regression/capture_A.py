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
def _strip_html(raw):
    return re.sub(r"<[^>]+>", "", raw).strip() if raw else None


def _title(html):
    m = re.search(r"<title>([^<]+)</title>", html)
    return m.group(1).strip() if m else None


def _h1(html):
    # h1s now often contain nested <i class="fas ..."> icons; strip inner tags.
    m = re.search(r'<h1[^>]*class="h2"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        return _strip_html(m.group(1))
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
    return _strip_html(m.group(1)) if m else None


def _renewable_key_rows(html):
    """Pull Status/Target values for a few well-known Renewable rows
    whose numbers are contractually stable (seed-fixed)."""
    rows = {}
    for code in ("9.3.1", "9.3.4", "10.1", "10.2"):
        # The badge contains the code; the row has multiple cells.
        # Pattern: find TR containing >code< then pick out the floatformat cells.
        pat = re.compile(
            rf'<tr[^>]*>(?:(?!</tr>).)*?>\s*{re.escape(code)}\s*<.*?</tr>',
            re.DOTALL,
        )
        m = pat.search(html)
        if not m:
            continue
        row_html = m.group(0)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        stripped = [_strip_html(c) for c in cells]
        if len(stripped) >= 5:
            rows[code] = {
                "status": stripped[3] or "",
                "target": stripped[4] or "",
            }
    return rows


def _bilanz_section_headers(html):
    return [_strip_html(m) for m in re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL)]


def _ws_headings(html):
    """Pull the Solar / Wind card headings — they're stable and German."""
    return [_strip_html(m) for m in re.findall(
        r'<div class="card-header[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL
    )]


def _dashboard_cards(html):
    """Pull card title -> h3 value pairs on /simulation/ regardless of order."""
    pairs = {}
    label_key = {
        "Flächennutzung": "flaechennutzung_count",
        "Erneuerbare Energien": "erneuerbare_count",
        "Verbrauch": "verbrauch_count",
        "Szenario-Abgleich": "szenario_abgleich_count",
    }
    # Match each <h5 class="card-title ..."> followed by its <h3> value.
    matches = re.findall(
        r'class="card-title[^"]*"[^>]*>([^<]+)</h5>\s*<h3[^>]*>\s*([^<]+?)\s*</h3>',
        html, re.DOTALL,
    )
    for title, value in matches:
        key = label_key.get(title.strip())
        if key:
            pairs[key] = value.strip()
    # Ensure all four keys exist (null if the page didn't render it).
    for v in label_key.values():
        pairs.setdefault(v, None)
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

    # /renewable/
    html = _get(opener, "/renewable/")
    out["pages"]["/renewable/"] = {
        "title": _title(html),
        "h1": _h1(html),
        "key_rows": _renewable_key_rows(html),
    }

    # /verbrauch/, /annual-electricity/, /cockpit/ — just title + h1.
    # Deep comparisons on these live in the dedicated test suites.
    for path in ["/verbrauch/", "/annual-electricity/", "/cockpit/"]:
        html = _get(opener, path)
        out["pages"][path] = {
            "title": _title(html),
            "h1": _h1(html),
        }

    # /bilanz/ — title + h1 + section headings (they contain stable text).
    html = _get(opener, "/bilanz/")
    out["pages"]["/bilanz/"] = {
        "title": _title(html),
        "h1": _h1(html),
        "section_headings": _bilanz_section_headers(html),
    }

    # /ws/ — title + h1 + card headers (stable German).
    html = _get(opener, "/ws/")
    out["pages"]["/ws/"] = {
        "title": _title(html),
        "h1": _h1(html),
        "card_headings": _ws_headings(html),
    }

    out_path = REPO / "verification" / str(date.today()) / "A-baseline-readonly.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out_path}")
    return out_path


if __name__ == "__main__":
    capture()
