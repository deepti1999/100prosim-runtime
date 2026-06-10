"""Modifikationsdetails page (Phase 6-B, T48–T52, PDF §2.5.5).

Renders the five variant-comparison charts from 100prosim-Excel
AH.Cockpit2, each with four series:

- Status          — the baseline values in the DB (status_* / status_value)
- Basisszenario   — the admin baseline snapshot (or Status if absent)
- Vorzustand      — the most recent ScenarioSnapshot or Basisszenario
- Aktueller Zustand — the live target_* / ziel / target_value

Data layout is pre-baked server-side so the template can render a
pure-data JSON payload that the client converts into Chart.js configs.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    BaselineSnapshot,
    LandUse,
    RenewableData,
    ScenarioSnapshot,
    VerbrauchData,
)

ADMIN_BASELINE_KEY = "global"


# --- Chart definitions ---------------------------------------------------
#
# Each chart entry describes:
#   title   — the German heading shown in the UI.
#   unit    — suffix shown in the y-axis / tooltip.
#   source  — "verbrauch" | "renewable" | "landuse" (pick the base queryset).
#   codes   — list of {code, label} — the x-axis rows to pull.
#
# Codes are stakeholder-contract names (never translated, per PDF §2.3).
# Some chart values intentionally use a display transform. Example:
# Renewable rows are stored in GWh/a, while the Cockpit chart is labelled
# TWh/a, so those values are divided by 1000 for display only.

CHARTS = [
    {
        "id": "chart_nachfrage_einfluesse",
        "title": "Nachfrage-Einflüsse auf Endenergieverbrauch (Variantenvergleich)",
        "unit": "GWh/a",
        "source": "verbrauch",
        "codes": [
            {"code": "1", "label": "KLIK"},
            {"code": "2.10", "label": "Gebäudewärme"},
            {"code": "3.7", "label": "Prozesswärme"},
            {"code": "6.0", "label": "Mobile Anwendungen"},
        ],
    },
    {
        "id": "chart_effizienz_einfluesse",
        "title": "Effizienz-Einflüsse auf Endenergieverbrauch (Variantenvergleich)",
        "unit": "%",
        "source": "verbrauch",
        "codes": [
            {"code": "1.1.2", "label": "Stromanwend.-Effizienz Haushalte"},
            {"code": "1.2.4", "label": "Stromanw.-Effiz. Handel/Dienstl."},
            {"code": "1.3.4", "label": "Stromanw.-Effiz. Gewerbe/Industrie"},
            {"code": "2.5.1", "label": "Warmwasser-Effizienz Gebäudewärme"},
            {"code": "3.1.1", "label": "Prozesswärme Haushalte"},
            {"code": "3.2.2", "label": "Prozesswärme Industrie/GHD"},
        ],
    },
    {
        "id": "chart_endenergie_anwendungen",
        "title": "Endenergie-Verbrauch nach Anwendungsbereichen inkl. Grundstoffe",
        "unit": "TWh/a",
        "source": "verbrauch",
        "scale": 0.001,
        "codes": [
            {"code": "1", "label": "KLIK"},
            {"code": "2.10", "label": "Gebäudewärme"},
            {"code": "3.7", "label": "Prozesswärme"},
            {"code": "6.0", "label": "Mobile Anwendungen"},
            {"code": "9.1.4", "label": "Grundstoffe"},
        ],
    },
    {
        "id": "chart_primaerenergie_quellen",
        "title": "Primärenergie-Beiträge nach Quellen",
        "unit": "TWh/a",
        "source": "renewable",
        "scale": 0.001,
        "codes": [
            {"code": "9.1.1", "label": "Wind onshore"},
            {"code": "9.1.2", "label": "Solar Freiflächen"},
            {"code": "9.1.3", "label": "Wasserkraft + Geothermie"},
            {"code": "9.1.4", "label": "Biobrennstoffe"},
        ],
    },
    {
        "id": "chart_ausbau_erneuerbare",
        "title": "Ausbau der Erneuerbaren Energiequellen",
        "unit": "%",
        "source": "landuse",
        "value_mode": "landuse_parent_percent",
        "codes": [
            {"code": "LU_2.1", "label": "Solar Freiflächen"},
            {"code": "LU_6", "label": "Wind onshore"},
        ],
    },
]


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scale(value, factor):
    number = _to_float(value)
    if number is None:
        return None
    return number * factor


def _snapshot_bucket(payload, source):
    if not payload:
        return []
    bucket = {
        "verbrauch": "verbrauch",
        "renewable": "renewable",
        "landuse": "landuse",
    }.get(source)
    if not bucket:
        return []
    return payload.get(bucket, []) or []


def _snapshot_lookup(payload, source, code, pick):
    """Helper: dig a value out of a snapshot payload.

    ``payload`` is the JSONField on BaselineSnapshot or ScenarioSnapshot,
    which was produced by baseline_api._snapshot_payload_for_owner.
    ``pick`` tells us which field to pull (status or target side).
    """
    for row in _snapshot_bucket(payload, source):
        if row.get("code") == code:
            return row.get(pick)
    return None


def _snapshot_landuse_parent_percent(payload, code, pick):
    """Return the same child/parent percentage shown on the land-use page."""
    by_code = {
        row.get("code"): row
        for row in _snapshot_bucket(payload, "landuse")
        if row.get("code")
    }
    child = by_code.get(code)
    if not child:
        return None
    parent_code = child.get("parent_code")
    parent = by_code.get(parent_code)
    if not parent:
        return None

    child_value = _to_float(child.get(pick))
    parent_value = _to_float(parent.get(pick))
    if child_value is None or not parent_value:
        return None
    return (child_value / parent_value) * 100.0


def _live_value(source, code, pick):
    """Read the current (live) value for a given source+code+field."""
    try:
        if source == "verbrauch":
            row = VerbrauchData.objects.filter(code=code).first()
            if not row:
                return None
            return getattr(row, pick, None)
        if source == "renewable":
            row = RenewableData.objects.filter(code=code).first()
            if not row:
                return None
            return getattr(row, pick, None)
        if source == "landuse":
            row = LandUse.objects.filter(code=code).first()
            if not row:
                return None
            return getattr(row, pick, None)
    except Exception:
        return None
    return None


def _live_landuse_parent_percent(code, pick):
    """Return child/parent land-use percentage from live rows."""
    try:
        row = LandUse.objects.select_related("parent").filter(code=code).first()
    except Exception:
        return None
    if not row or not row.parent:
        return None
    child_value = _to_float(getattr(row, pick, None))
    parent_value = _to_float(getattr(row.parent, pick, None))
    if child_value is None or not parent_value:
        return None
    return (child_value / parent_value) * 100.0


def _chart_live_value(chart, code, pick):
    if chart.get("value_mode") == "landuse_parent_percent":
        return _live_landuse_parent_percent(code, pick)
    return _scale(_live_value(chart["source"], code, pick), chart.get("scale", 1.0))


def _chart_snapshot_value(chart, payload, code, pick):
    if chart.get("value_mode") == "landuse_parent_percent":
        return _snapshot_landuse_parent_percent(payload, code, pick)
    return _scale(_snapshot_lookup(payload, chart["source"], code, pick), chart.get("scale", 1.0))


@login_required
def modifikationsdetails_view(request):
    # Resolve baselines.
    admin_baseline = BaselineSnapshot.objects.filter(key=ADMIN_BASELINE_KEY).first()
    admin_payload = admin_baseline.payload if admin_baseline else None

    # Vorzustand: the most recent ScenarioSnapshot owned by the user.
    last_scenario = (
        ScenarioSnapshot.objects
        .filter(owner=request.user)
        .order_by("-updated_at")
        .first()
    )
    vorzustand_payload = last_scenario.payload if last_scenario else admin_payload

    series_spec = {
        # (source -> (status_field, target_field))
        "verbrauch": ("status", "ziel"),
        "renewable": ("status_value", "target_value"),
        "landuse": ("status_ha", "target_ha"),
    }

    charts_payload = []
    for chart in CHARTS:
        status_field, target_field = series_spec[chart["source"]]

        status = []
        basis = []
        vor = []
        current = []

        for entry in chart["codes"]:
            code = entry["code"]
            status.append(_chart_live_value(chart, code, status_field))
            basis.append(_chart_snapshot_value(chart, admin_payload, code, target_field))
            vor.append(_chart_snapshot_value(chart, vorzustand_payload, code, target_field))
            current.append(_chart_live_value(chart, code, target_field))

        charts_payload.append({
            "id": chart["id"],
            "title": chart["title"],
            "unit": chart["unit"],
            "labels": [e["label"] for e in chart["codes"]],
            "series": {
                "status": status,
                "basisszenario": basis,
                "vorzustand": vor,
                "aktuell": current,
            },
        })

    context = {
        "charts": charts_payload,
        "admin_baseline_available": admin_baseline is not None,
        "vorzustand_source": (
            "Szenario: " + last_scenario.name if last_scenario else
            "Basisszenario" if admin_baseline else "—"
        ),
        "current_section": "modifikationsdetails",
    }
    return render(request, "simulator/modifikationsdetails.html", context)
