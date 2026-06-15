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
BAR_SCALE_MAX = 120.0
EFFICIENCY_BAR_SCALE_MAX = 150.0


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


def _bar_width(value, scale_max=BAR_SCALE_MAX):
    number = _to_float(value)
    if number is None:
        return "0"
    width = max(0.0, min((number / scale_max) * 100.0, 100.0))
    return f"{width:.3f}".rstrip("0").rstrip(".")


def _format_percent_value(value):
    number = _to_float(value)
    if number is None:
        return "—"
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".replace(".", ",")


def _comparison_row(label, *, status, basis, current, scale_max=BAR_SCALE_MAX):
    status_value = _to_float(status)
    current_value = _to_float(current)
    delta = None
    if status_value is not None and current_value is not None:
        delta = current_value - status_value
    return {
        "label": label,
        "status": _format_percent_value(status),
        "basis": _format_percent_value(basis),
        "current": _format_percent_value(current),
        "status_width": _bar_width(status, scale_max),
        "basis_width": _bar_width(basis, scale_max),
        "current_width": _bar_width(current, scale_max),
        "delta": (
            "—"
            if delta is None
            else f"{'+' if delta >= 0 else ''}{_format_percent_value(delta)} %"
        ),
    }


def _global_verbrauch_value(code, field):
    try:
        from simulator.region_scope import get_current_region_code

        qs = VerbrauchData.all_objects.filter(
            owner__isnull=True,
            code=code,
        )
        region_code = get_current_region_code()
        if region_code:
            qs = qs.filter(region__code=region_code)
        row = qs.first()
    except Exception:
        return None
    return getattr(row, field, None) if row else None


def _scoped_verbrauch_value(code, field):
    try:
        row = VerbrauchData.objects.filter(code=code).first()
    except Exception:
        return None
    return getattr(row, field, None) if row else None


def _verbrauch_comparison_row(label, code, *, scale_max=BAR_SCALE_MAX):
    status = _global_verbrauch_value(code, "status")
    basis = _global_verbrauch_value(code, "ziel")
    current = _scoped_verbrauch_value(code, "ziel")
    return _comparison_row(
        label,
        status=status if status is not None else 100.0,
        basis=basis if basis is not None else 100.0,
        current=current if current is not None else basis,
        scale_max=scale_max,
    )


def _modification_comparison_rows():
    wohn_status = _global_verbrauch_value("2.1.2", "status")
    wohn_basis = _global_verbrauch_value("2.1.2", "ziel")
    wohn_current = _scoped_verbrauch_value("2.1.2", "ziel")
    gewerbe_status = _global_verbrauch_value("2.2.1", "status")
    gewerbe_basis = _global_verbrauch_value("2.2.1", "ziel")
    gewerbe_current = _scoped_verbrauch_value("2.2.1", "ziel")
    handel_status = _global_verbrauch_value("1.2.2", "status")
    handel_basis = _global_verbrauch_value("1.2.2", "ziel")
    handel_current = _scoped_verbrauch_value("1.2.2", "ziel")
    industrie_status = _global_verbrauch_value("3.2.1", "status")
    industrie_basis = _global_verbrauch_value("3.2.1", "ziel")
    industrie_current = _scoped_verbrauch_value("3.2.1", "ziel")
    kunststoff_status = _global_verbrauch_value("9.1.1", "status")
    kunststoff_basis = _global_verbrauch_value("9.1.1", "ziel")
    kunststoff_current = _scoped_verbrauch_value("9.1.1", "ziel")
    personen_status = _global_verbrauch_value("4.1.1.1", "status")
    personen_basis = _global_verbrauch_value("4.1.1.1", "ziel")
    personen_current = _scoped_verbrauch_value("4.1.1.1", "ziel")
    gueter_status = _global_verbrauch_value("4.1.2.1", "status")
    gueter_basis = _global_verbrauch_value("4.1.2.1", "ziel")
    gueter_current = _scoped_verbrauch_value("4.1.2.1", "ziel")
    luft_status = _global_verbrauch_value("5.1", "status")
    luft_basis = _global_verbrauch_value("5.1", "ziel")
    luft_current = _scoped_verbrauch_value("5.1", "ziel")

    return [
        _comparison_row(
            "Bevölkerung / Verbraucher",
            status=100.0,
            basis=100.0,
            current=100.0,
        ),
        _comparison_row(
            "Wohnfläche/Pers.",
            status=wohn_status if wohn_status is not None else 100.0,
            basis=wohn_basis if wohn_basis is not None else 100.0,
            current=wohn_current if wohn_current is not None else wohn_basis,
        ),
        _comparison_row(
            "Gewerbefläche/Pers.",
            status=gewerbe_status if gewerbe_status is not None else 100.0,
            basis=gewerbe_basis if gewerbe_basis is not None else 100.0,
            current=gewerbe_current if gewerbe_current is not None else gewerbe_basis,
        ),
        _comparison_row(
            "Handels-/Dienstleistungsvol./Pers.",
            status=handel_status if handel_status is not None else 100.0,
            basis=handel_basis if handel_basis is not None else 100.0,
            current=handel_current if handel_current is not None else handel_basis,
        ),
        _comparison_row(
            "Industrie/Gewerbe-Produkt.Vol./Pers.",
            status=industrie_status if industrie_status is not None else 100.0,
            basis=industrie_basis if industrie_basis is not None else 100.0,
            current=industrie_current if industrie_current is not None else industrie_basis,
        ),
        _comparison_row(
            "Kunststofferzeugung/Pers.",
            status=kunststoff_status if kunststoff_status is not None else 100.0,
            basis=kunststoff_basis if kunststoff_basis is not None else 100.0,
            current=kunststoff_current if kunststoff_current is not None else kunststoff_basis,
        ),
        _comparison_row(
            "Personenverkehrsleistung /Pers.",
            status=personen_status if personen_status is not None else 100.0,
            basis=personen_basis if personen_basis is not None else 100.0,
            current=personen_current if personen_current is not None else personen_basis,
        ),
        _comparison_row(
            "Güterverkehrsleistung /Pers.",
            status=gueter_status if gueter_status is not None else 100.0,
            basis=gueter_basis if gueter_basis is not None else 100.0,
            current=gueter_current if gueter_current is not None else gueter_basis,
        ),
        _comparison_row(
            "Luftverkehrsleistung / Pers.",
            status=luft_status if luft_status is not None else 100.0,
            basis=luft_basis if luft_basis is not None else 100.0,
            current=luft_current if luft_current is not None else luft_basis,
        ),
    ]


def _efficiency_comparison_rows():
    return [
        _verbrauch_comparison_row(
            "Stromanwend.-Effizienz Haushalte",
            "1.1.2",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
        _verbrauch_comparison_row(
            "Stromanw.-Effiz.Handel/Dienstl.",
            "1.2.4",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
        _verbrauch_comparison_row(
            "Stromanw.-Effiz.Gewerbe/Industrie",
            "1.3.4",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
    ]


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
        "comparison_rows": _modification_comparison_rows(),
        "efficiency_rows": _efficiency_comparison_rows(),
        "current_section": "modifikationsdetails",
    }
    return render(request, "simulator/modifikationsdetails.html", context)
