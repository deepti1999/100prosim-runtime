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
ENDENERGIE_STACK_SCALE_MAX = 3000.0
PRIMARY_STACK_SCALE_MAX = 3500.0
PRIMARY_STATUS_TOTAL_TWH = 3199.0
COCKPIT_STACK_SCALE_MAX = 3500.0
EXPANSION_PCT_SCALE_MAX = 25.0


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
            {
                "code": "9.1.4",
                "status_code": "9.1.2",
                "target_code": "9.1.4",
                "label": "Grundstoffe",
            },
        ],
    },
    {
        "id": "chart_primaerenergie_quellen",
        "title": "Primärenergie-Beiträge nach Quellen",
        "unit": "TWh/a",
        "source": "renewable",
        "scale": 0.001,
        "codes": [
            {"code": "2.1.1.2.2", "label": "Wind onshore"},
            {"code": "2.2.1.2.3", "label": "Wind offshore"},
            {"code": "9.1.2", "label": "Solar Freiflächen"},
            {"code": "9.1.3", "label": "Wasserkraft + Geothermie"},
            {"code": "10.9.1.1", "label": "Biobrennstoffe gasförmig"},
            {"code": "10.9.1.2", "label": "Biobrennstoffe flüssig"},
            {"code": "10.9.1.3", "label": "Biobrennstoffe fest"},
            {"code": "7.1.2.3", "label": "Umgebungswärme Luft"},
            {"code": "7.1.4.3", "label": "Umgebungswärme Erde"},
            {"code": "1.1.1.1.2", "label": "Solarwärme"},
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


def _stack_width(value, total):
    number = _to_float(value)
    total_number = _to_float(total)
    if number is None or not total_number:
        return "0"
    width = max(0.0, min((number / total_number) * 100.0, 100.0))
    return f"{width:.3f}".rstrip("0").rstrip(".")


def _format_percent_value(value):
    number = _to_float(value)
    if number is None:
        return "—"
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".replace(".", ",")


def _format_ratio_value(value):
    number = _to_float(value)
    if number is None:
        return "—"
    return f"{number:.1f}".replace(".", ",")


def _format_decimal_value(value, decimals=1):
    number = _to_float(value)
    if number is None:
        return "—"
    if decimals == 0:
        return str(int(round(number)))
    return f"{number:.{decimals}f}".replace(".", ",")


def _format_signed_percent(value, *, zero_style="+-0"):
    number = _to_float(value)
    if number is None:
        return "—"
    if abs(number) < 0.05:
        return f"{zero_style} %"
    sign = "+" if number > 0 else ""
    return f"{sign}{int(round(number))} %"


def _comparison_delta(status, current, mode="difference"):
    status_value = _to_float(status)
    current_value = _to_float(current)
    if status_value is None or current_value is None:
        return "—"
    if mode == "ratio":
        if status_value == 0.0:
            return "(Neu)" if current_value else "x 0,0"
        return f"x {_format_ratio_value(current_value / status_value)}"
    delta = current_value - status_value
    return f"{'+' if delta >= 0 else ''}{_format_percent_value(delta)} %"


def _percent_change(status, target):
    status_value = _to_float(status)
    target_value = _to_float(target)
    if status_value is None or target_value is None or status_value == 0:
        return None
    return ((target_value / status_value) - 1.0) * 100.0


def _verbrauch_percent_change(status_code, target_code=None):
    return _percent_change(
        _global_verbrauch_value(status_code, "status"),
        _scoped_verbrauch_value(target_code or status_code, "ziel"),
    )


def _comparison_row(label, *, status, basis, current, scale_max=BAR_SCALE_MAX, delta_mode="difference"):
    return {
        "label": label,
        "status": _format_percent_value(status),
        "basis": _format_percent_value(basis),
        "current": _format_percent_value(current),
        "status_width": _bar_width(status, scale_max),
        "basis_width": _bar_width(basis, scale_max),
        "current_width": _bar_width(current, scale_max),
        "delta": _comparison_delta(status, current, delta_mode),
    }


def _endenergie_segment_values(payload=None, target=False):
    field = "ziel" if target else "status"
    source = _snapshot_lookup if payload else None

    def value(code, pick):
        raw = source(payload, "verbrauch", code, pick) if source else _live_value("verbrauch", code, pick)
        return _scale(raw, 0.001)

    return {
        "klik": value("1", field),
        "gw": value("2.10", field),
        "pw": value("3.7", field),
        "grund": value("9.1.4" if target else "9.1.2", "ziel" if target else "status"),
        "ma": value("6.0", field),
    }


def _endenergie_stack_row(label, values, status_total=None):
    total = sum(value for value in values.values() if value is not None)
    delta = ""
    if status_total and label == "Aktueller Zustand":
        percent = ((total - status_total) / status_total) * 100.0
        delta = f"{'+' if percent >= 0 else ''}{_format_percent_value(percent)} %"
    return {
        "label": label,
        "width": _bar_width(total, ENDENERGIE_STACK_SCALE_MAX),
        "delta": delta,
        "segments": {
            name: _stack_width(value, total)
            for name, value in values.items()
        },
    }


def _endenergie_stack_rows(admin_payload=None, vorzustand_payload=None):
    status_values = _endenergie_segment_values(target=False)
    basis_values = _endenergie_segment_values(admin_payload, target=True)
    vor_values = _endenergie_segment_values(vorzustand_payload, target=True)
    current_values = _endenergie_segment_values(target=True)
    status_total = sum(value for value in status_values.values() if value is not None)
    return [
        _endenergie_stack_row("Status", status_values),
        _endenergie_stack_row("Basisszenario", basis_values),
        _endenergie_stack_row("Vorzustand", vor_values),
        _endenergie_stack_row("Aktueller Zustand", current_values, status_total=status_total),
    ]


def _renewable_twh(code, field, payload=None):
    raw = (
        _snapshot_lookup(payload, "renewable", code, field)
        if payload
        else _live_value("renewable", code, field)
    )
    return _scale(raw, 0.001)


def _sum_values(*values):
    numeric = [_to_float(value) for value in values]
    present = [value for value in numeric if value is not None]
    if len(present) != len(values):
        return None
    return sum(present)


def _primaerenergie_segment_values(payload=None, target=False):
    field = "target_value" if target else "status_value"
    wind_on = _renewable_twh("2.1.1.2.2", field, payload)
    if wind_on is None:
        wind_on = _renewable_twh("9.1.1", field, payload)
    wind_off = _renewable_twh("2.2.1.2.3", field, payload)
    pv = _renewable_twh("9.1.2", field, payload)
    water = _renewable_twh("9.1.3", field, payload)
    bio = _sum_values(
        _renewable_twh("10.9.1.1", field, payload),
        _renewable_twh("10.9.1.2", field, payload),
        _renewable_twh("10.9.1.3", field, payload),
    )
    heat = _sum_values(
        _renewable_twh("7.1.2.3", field, payload),
        _renewable_twh("7.1.4.3", field, payload),
        _renewable_twh("1.1.1.1.2", field, payload),
    )
    values = {
        "wind_on": wind_on,
        "wind_off": wind_off,
        "pv": pv,
        "water": water,
        "bio": bio,
        "heat": heat,
    }
    renewable_total = sum(value for value in values.values() if value is not None)
    total = renewable_total if target else PRIMARY_STATUS_TOTAL_TWH
    values["fossil"] = max(total - renewable_total, 0.0)
    return values


def _primaerenergie_stack_row(label, values, status_total=None):
    total = sum(value for value in values.values() if value is not None)
    delta = ""
    if status_total and label == "Aktueller Zustand":
        percent = ((total - status_total) / status_total) * 100.0
        delta = f"{'+' if percent >= 0 else ''}{_format_percent_value(percent)} %"
    return {
        "label": label,
        "width": _bar_width(total, PRIMARY_STACK_SCALE_MAX),
        "delta": delta,
        "segments": {
            name: _stack_width(value, total)
            for name, value in values.items()
        },
    }


def _primaerenergie_stack_rows(admin_payload=None, vorzustand_payload=None):
    status_values = _primaerenergie_segment_values(target=False)
    basis_values = _primaerenergie_segment_values(admin_payload, target=True)
    vor_values = _primaerenergie_segment_values(vorzustand_payload, target=True)
    current_values = _primaerenergie_segment_values(target=True)
    status_total = sum(value for value in status_values.values() if value is not None)
    return [
        _primaerenergie_stack_row("Status", status_values),
        _primaerenergie_stack_row("Basisszenario", basis_values),
        _primaerenergie_stack_row("Vorzustand", vor_values),
        _primaerenergie_stack_row("Aktueller Zustand", current_values, status_total=status_total),
    ]


def _cockpit_vertical_bar(label, values, segment_order, *, label_tone="current"):
    total = sum(value for value in values.values() if value is not None)
    return {
        "label": label,
        "height": _bar_width(total, COCKPIT_STACK_SCALE_MAX),
        "label_tone": label_tone,
        "segments": [
            {
                "name": name,
                "class_name": name.replace("_", "-"),
                "height": _stack_width(values.get(name), total),
            }
            for name in segment_order
        ],
    }


def _cockpit_energy_bars():
    consumption_order = ["klik", "gw", "pw", "grund", "ma"]
    production_order = ["fossil", "wind_on", "wind_off", "pv", "water", "bio", "heat"]
    return [
        _cockpit_vertical_bar(
            "Status",
            _endenergie_segment_values(target=False),
            consumption_order,
            label_tone="status",
        ),
        _cockpit_vertical_bar(
            "Ziel",
            _endenergie_segment_values(target=True),
            consumption_order,
        ),
        _cockpit_vertical_bar(
            "Status",
            _primaerenergie_segment_values(target=False),
            production_order,
            label_tone="status",
        ),
        _cockpit_vertical_bar(
            "Ziel",
            _primaerenergie_segment_values(target=True),
            production_order,
        ),
    ]


def _cockpit_effect(label, short_label, thumb_class, total, sufficiency=None, sufficiency_label="", efficiency_label=""):
    suff = _to_float(sufficiency)
    total_value = _to_float(total)
    efficiency = None
    if total_value is not None:
        efficiency = total_value - (suff if suff is not None else 0.0)
    rows = []
    if sufficiency_label:
        rows.append({
            "value": _format_signed_percent(suff if suff is not None else 0.0),
            "label": sufficiency_label,
        })
    if efficiency_label:
        rows.append({
            "value": _format_signed_percent(efficiency),
            "label": efficiency_label,
        })
    return {
        "label": label,
        "short_label": short_label,
        "thumb_class": thumb_class,
        "total": _format_signed_percent(total_value, zero_style="0"),
        "rows": rows,
    }


def _cockpit_effect_rows():
    mobile_total = _verbrauch_percent_change("6.0")
    mobile_suff = _verbrauch_percent_change("4.1.1.1")
    gw_total = _verbrauch_percent_change("2.10")
    gw_suff = _verbrauch_percent_change("2.1.2")
    pw_total = _verbrauch_percent_change("3.7")
    pw_suff = _verbrauch_percent_change("3.2.1")
    grund_total = _verbrauch_percent_change("9.1.2", "9.1.4")
    grund_suff = _verbrauch_percent_change("9.1.1")
    klik_total = _verbrauch_percent_change("1.4")

    return [
        _cockpit_effect(
            "Mobile Anwendungen",
            "MA",
            "mod-thumb-ma",
            mobile_total,
            mobile_suff,
            "Suffizienz (Pkm/Pers.)",
            "Effizienz (kWh/Pkm)",
        ),
        _cockpit_effect(
            "Gebäudewärme",
            "GW",
            "mod-thumb-gw",
            gw_total,
            gw_suff,
            "Suffizienz (qm/Pers.)",
            "Effizienz (Wärmeschutz, San.-Rate)",
        ),
        _cockpit_effect(
            "Prozesswärme",
            "PW",
            "mod-thumb-pw",
            pw_total,
            pw_suff,
            "Suffizienz (Prod.Vol./Pers.)",
            "Effizienz (Produktions-Proz.)",
        ),
        _cockpit_effect(
            "Grundstoffe",
            "GS",
            "mod-thumb-gs",
            grund_total,
            grund_suff,
            "Suffizienz (Kunststoff-Vol./Pers.)",
            "Effizienz (Kunststoff-Recycling)",
        ),
        _cockpit_effect(
            "Strom-Anwend.",
            "KLIK*",
            "mod-thumb-klik",
            klik_total,
            0.0,
            "Suffizienz (El. Geräte/Pers.)",
            "Effizienz (Elektrische Geräte)",
        ),
        {
            "label": "Bevölkerungsentwicklung",
            "short_label": "",
            "thumb_class": "mod-thumb-pop",
            "total": "0 %",
            "rows": [],
        },
    ]


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


def _global_renewable_value(code, field):
    try:
        from simulator.region_scope import get_current_region_code

        qs = RenewableData.all_objects.filter(
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


def _scoped_renewable_value(code, field):
    try:
        row = RenewableData.objects.filter(code=code).first()
    except Exception:
        return None
    return getattr(row, field, None) if row else None


def _global_landuse_value(code, field):
    try:
        from simulator.region_scope import get_current_region_code

        qs = LandUse.all_objects.filter(
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


def _scoped_landuse_value(code, field):
    try:
        row = LandUse.objects.filter(code=code).first()
    except Exception:
        return None
    return getattr(row, field, None) if row else None


def _landuse_percent_of_value(code, denominator_code, field, payload=None, *, scoped=False):
    if payload:
        numerator = _snapshot_lookup(payload, "landuse", code, field)
        denominator = _snapshot_lookup(payload, "landuse", denominator_code, field)
    elif scoped:
        numerator = _scoped_landuse_value(code, field)
        denominator = _scoped_landuse_value(denominator_code, field)
    else:
        numerator = _global_landuse_value(code, field)
        denominator = _global_landuse_value(denominator_code, field)
    numerator = _to_float(numerator)
    denominator = _to_float(denominator)
    if numerator is None or not denominator:
        return None
    return (numerator / denominator) * 100.0


def _landuse_energy_crop_percent(field, payload=None, *, scoped=False):
    crop_codes = ("LU_2.2.2", "LU_2.2.3", "LU_2.2.4", "LU_2.2.5")
    if payload:
        crop_values = [_snapshot_lookup(payload, "landuse", code, field) for code in crop_codes]
        denominator = _snapshot_lookup(payload, "landuse", "LU_2", field)
    elif scoped:
        crop_values = [_scoped_landuse_value(code, field) for code in crop_codes]
        denominator = _scoped_landuse_value("LU_2", field)
    else:
        crop_values = [_global_landuse_value(code, field) for code in crop_codes]
        denominator = _global_landuse_value("LU_2", field)
    total = _sum_values(*crop_values)
    denominator = _to_float(denominator)
    if total is None or not denominator:
        return None
    return (total / denominator) * 100.0


def _renewable_gw_value(code, field, payload=None, *, scoped=False):
    if payload:
        raw = _snapshot_lookup(payload, "renewable", code, field)
    elif scoped:
        raw = _scoped_renewable_value(code, field)
    else:
        raw = _global_renewable_value(code, field)
    return _scale(raw, 0.001)


def _renewable_gw_sum(codes, field, payload=None, *, scoped=False):
    values = [_renewable_gw_value(code, field, payload, scoped=scoped) for code in codes]
    return _sum_values(*values)


def _expansion_width(value, scale_max):
    return _bar_width(value, scale_max)


def _expansion_delta(status, current):
    return _comparison_delta(status, current, mode="ratio")


def _expansion_row(
    subtitle,
    *,
    unit,
    scale,
    status,
    basis,
    vorzustand,
    current,
    label_template,
    scale_max,
    potential_segments=None,
    outline=False,
    decimals=1,
):
    return {
        "subtitle": subtitle,
        "unit": unit,
        "scale": scale,
        "label": label_template.format(value=_format_decimal_value(current if current is not None else basis, decimals)),
        "status_label": _format_decimal_value(status, decimals),
        "current_label": _format_decimal_value(current if current is not None else basis, decimals),
        "delta": _expansion_delta(status, current if current is not None else basis),
        "outline": outline,
        "potential_segments": potential_segments or [],
        "status_width": _expansion_width(status, scale_max),
        "basis_width": _expansion_width(basis, scale_max),
        "vor_width": _expansion_width(vorzustand if vorzustand is not None else basis, scale_max),
        "current_width": _expansion_width(current if current is not None else basis, scale_max),
    }


def _section4_expansion_rows(admin_payload=None, vorzustand_payload=None):
    potential_10 = [
        {"class": "mod-seg-saved", "width": "5"},
        {"class": "mod-seg-sufficient", "width": "37"},
        {"class": "mod-seg-thinkable", "width": "38"},
        {"class": "mod-seg-hopeless", "width": "20"},
    ]
    potential_120 = [
        {"class": "mod-seg-saved", "width": "10"},
        {"class": "mod-seg-sufficient", "width": "58"},
        {"class": "mod-seg-thinkable", "width": "12"},
        {"class": "mod-seg-hopeless", "width": "20"},
    ]
    potential_12 = [
        {"class": "mod-seg-saved", "width": "8"},
        {"class": "mod-seg-sufficient", "width": "38"},
        {"class": "mod-seg-thinkable", "width": "30"},
        {"class": "mod-seg-hopeless", "width": "24"},
    ]
    potential_25_solar = [
        {"class": "mod-seg-saved", "width": "8"},
        {"class": "mod-seg-sufficient", "width": "48"},
        {"class": "mod-seg-thinkable", "width": "36"},
        {"class": "mod-seg-hopeless", "width": "8"},
    ]
    potential_25_crops = [
        {"class": "mod-seg-saved", "width": "8"},
        {"class": "mod-seg-sufficient", "width": "50"},
        {"class": "mod-seg-thinkable", "width": "32"},
        {"class": "mod-seg-hopeless", "width": "10"},
    ]

    def landuse_row(subtitle, code, denominator_code, label_template, scale, scale_max, potential, *, outline=False):
        return _expansion_row(
            subtitle,
            unit=scale["unit"],
            scale=scale["ticks"],
            status=_landuse_percent_of_value(code, denominator_code, "status_ha"),
            basis=_landuse_percent_of_value(code, denominator_code, "target_ha", admin_payload),
            vorzustand=_landuse_percent_of_value(code, denominator_code, "target_ha", vorzustand_payload),
            current=_landuse_percent_of_value(code, denominator_code, "target_ha", scoped=True),
            label_template=label_template,
            scale_max=scale_max,
            potential_segments=potential,
            outline=outline,
        )

    def renewable_row(subtitle, codes, label_template, scale, scale_max, potential=None):
        code_list = tuple(codes) if isinstance(codes, (list, tuple)) else (codes,)

        def value(field, payload=None, scoped=False):
            if len(code_list) == 1:
                return _renewable_gw_value(code_list[0], field, payload, scoped=scoped)
            return _renewable_gw_sum(code_list, field, payload, scoped=scoped)

        return _expansion_row(
            subtitle,
            unit=scale["unit"],
            scale=scale["ticks"],
            status=value("status_value"),
            basis=value("target_value", admin_payload),
            vorzustand=value("target_value", vorzustand_payload),
            current=value("target_value", scoped=True),
            label_template=label_template,
            scale_max=scale_max,
            potential_segments=potential or [],
        )

    energy_crop_status = _landuse_energy_crop_percent("status_ha")
    energy_crop_basis = _landuse_energy_crop_percent("target_ha", admin_payload)
    energy_crop_vor = _landuse_energy_crop_percent("target_ha", vorzustand_payload)
    energy_crop_current = _landuse_energy_crop_percent("target_ha", scoped=True)

    return [
        {
            "title": "5.1 Windenergie onshore",
            "rows": [
                landuse_row(
                    "Windparkfläche",
                    "LU_6",
                    "LU_0",
                    "{value} % der Regionsfläche",
                    {"unit": "% v.Bodenfläche der Zielregion:", "ticks": ["0", "2", "4", "6", "8", "10"]},
                    10.0,
                    potential_10,
                ),
                renewable_row(
                    "Installierte Leistung",
                    "2.1.1.2",
                    "{value} GW",
                    {"unit": "[GW]", "ticks": ["0", "50", "100", "150", "200"]},
                    200.0,
                ),
            ],
        },
        {
            "title": "4.2 Windenergie offshore Deutschland (anteilige Anrechnung)",
            "rows": [
                renewable_row(
                    "Install. Leistung ges.",
                    "2.2.1",
                    "{value} GW",
                    {"unit": "", "ticks": ["0", "20", "40", "60", "80", "100", "120"]},
                    120.0,
                    potential_120,
                ),
            ],
        },
        {
            "title": "4.3 Solarenergie",
            "rows": [
                landuse_row(
                    "Solar-Dachflächen",
                    "LU_1.1",
                    "LU_1",
                    "{value} % v. Siedlungsfläche",
                    {"unit": "% von Siedlungsfläche:", "ticks": ["0", "2", "4", "6", "8", "10", "12"]},
                    12.0,
                    potential_12,
                ),
                landuse_row(
                    "Solar-Freiflächen",
                    "LU_2.1",
                    "LU_2",
                    "{value} % v. Landwirtsch.fläche",
                    {"unit": "% von Landwirtschaftsfläche:", "ticks": ["0", "5", "10", "15", "20", "25"]},
                    EXPANSION_PCT_SCALE_MAX,
                    potential_25_solar,
                    outline=True,
                ),
                renewable_row(
                    "Installierte Solarstrom-Leistung",
                    ("1.1.2.1.2.2", "1.2.1.2.2"),
                    "{value} GW",
                    {"unit": "[GW]", "ticks": ["0", "200", "400", "600", "800", "1.000", "1.200", "1.400"]},
                    1400.0,
                ),
            ],
        },
        {
            "title": "4.4 Energiepflanzenanbau",
            "rows": [
                _expansion_row(
                    "Anbaufläche",
                    unit="% von Landwirtschaftsfläche:",
                    scale=["0", "5", "10", "15", "20", "25"],
                    status=energy_crop_status,
                    basis=energy_crop_basis,
                    vorzustand=energy_crop_vor,
                    current=energy_crop_current,
                    label_template="{value} % v. Landwirtsch.fläche",
                    scale_max=EXPANSION_PCT_SCALE_MAX,
                    potential_segments=potential_25_crops,
                    outline=True,
                ),
            ],
        },
    ]


def _verbrauch_comparison_row(label, code, *, scale_max=BAR_SCALE_MAX, delta_mode="difference"):
    status = _global_verbrauch_value(code, "status")
    basis = _global_verbrauch_value(code, "ziel")
    current = _scoped_verbrauch_value(code, "ziel")
    return _comparison_row(
        label,
        status=status if status is not None else 100.0,
        basis=basis if basis is not None else 100.0,
        current=current if current is not None else basis,
        scale_max=scale_max,
        delta_mode=delta_mode,
    )


def _renovation_standard_percent(status_kwh, value_kwh):
    status = _to_float(status_kwh)
    value = _to_float(value_kwh)
    if status in (None, 0.0) or value is None:
        return None
    return (value / status) * 100.0


def _renovation_effect_value(standard_percent, renovated_share_percent):
    standard = _to_float(standard_percent)
    share = _to_float(renovated_share_percent)
    if standard is None or share is None:
        return None
    return 100.0 + (standard - 100.0) * (share / 100.0)


def _building_renovation_comparison_row(*, scale_max=EFFICIENCY_BAR_SCALE_MAX):
    standard_status_kwh = _global_verbrauch_value("2.4.1", "status")
    standard_basis_kwh = _global_verbrauch_value("2.4.1", "ziel")
    standard_current_kwh = _scoped_verbrauch_value("2.4.1", "ziel")

    share_status = _global_verbrauch_value("2.4.5", "status")
    share_basis = _global_verbrauch_value("2.4.5", "ziel")
    share_current = _scoped_verbrauch_value("2.4.5", "ziel")

    status_standard = _renovation_standard_percent(standard_status_kwh, standard_status_kwh)
    basis_standard = _renovation_standard_percent(standard_status_kwh, standard_basis_kwh)
    current_standard = _renovation_standard_percent(
        standard_status_kwh,
        standard_current_kwh if standard_current_kwh is not None else standard_basis_kwh,
    )

    return _comparison_row(
        "Energet.Sanierung Gebäudebestand",
        status=_renovation_effect_value(status_standard, share_status if share_status is not None else 0.0),
        basis=_renovation_effect_value(basis_standard, share_basis if share_basis is not None else 0.0),
        current=_renovation_effect_value(
            current_standard,
            share_current if share_current is not None else share_basis,
        ),
        scale_max=scale_max,
    )


def _heat_pump_share_value(air_value, ground_value, building_heat_value):
    air = _to_float(air_value)
    ground = _to_float(ground_value)
    building_heat = _to_float(building_heat_value)
    if air is None or ground is None or not building_heat:
        return None
    return ((air + ground) / building_heat) * 100.0


def _heat_pump_comparison_row(*, scale_max=EFFICIENCY_BAR_SCALE_MAX):
    status = _heat_pump_share_value(
        _global_renewable_value("7.1.2.2", "status_value"),
        _global_renewable_value("7.1.4.2", "status_value"),
        _global_verbrauch_value("2.10", "status"),
    )
    basis = _heat_pump_share_value(
        _global_renewable_value("7.1.2.2", "target_value"),
        _global_renewable_value("7.1.4.2", "target_value"),
        _global_verbrauch_value("2.10", "ziel"),
    )
    current = _heat_pump_share_value(
        _scoped_renewable_value("7.1.2.2", "target_value"),
        _scoped_renewable_value("7.1.4.2", "target_value"),
        _scoped_verbrauch_value("2.10", "ziel"),
    )
    return _comparison_row(
        "Wärmepumpenant.an Gebäudew.",
        status=status,
        basis=basis,
        current=current if current is not None else basis,
        delta_mode="ratio",
        scale_max=scale_max,
    )


def _solar_thermal_share_value(solar_thermal_value, building_heat_value):
    solar_thermal = _to_float(solar_thermal_value)
    building_heat = _to_float(building_heat_value)
    if solar_thermal is None or not building_heat:
        return None
    return (solar_thermal / building_heat) * 100.0


def _solar_thermal_comparison_row(*, scale_max=EFFICIENCY_BAR_SCALE_MAX):
    status = _solar_thermal_share_value(
        _global_renewable_value("1.1.1.1.2", "status_value"),
        _global_verbrauch_value("2.10", "status"),
    )
    basis = _solar_thermal_share_value(
        _global_renewable_value("1.1.1.1.2", "target_value"),
        _global_verbrauch_value("2.10", "ziel"),
    )
    current = _solar_thermal_share_value(
        _scoped_renewable_value("1.1.1.1.2", "target_value"),
        _scoped_verbrauch_value("2.10", "ziel"),
    )
    return _comparison_row(
        "Solarthermieanteil an Gebäudew.",
        status=status,
        basis=basis,
        current=current if current is not None else basis,
        delta_mode="ratio",
        scale_max=scale_max,
    )


def _biofuel_share_value(wood_total_value, wood_share_percent, building_heat_value):
    wood = _to_float(wood_total_value)
    share = _to_float(wood_share_percent)
    building_heat = _to_float(building_heat_value)
    if wood is None or share is None or not building_heat:
        return None
    return (wood * share) / building_heat


def _biofuel_comparison_row(*, scale_max=EFFICIENCY_BAR_SCALE_MAX):
    status = _biofuel_share_value(
        _global_renewable_value("4.1.3", "status_value"),
        _global_renewable_value("4.1.3.1", "status_value"),
        _global_verbrauch_value("2.10", "status"),
    )
    basis = _biofuel_share_value(
        _global_renewable_value("4.1.3", "target_value"),
        _global_renewable_value("4.1.3.1", "target_value"),
        _global_verbrauch_value("2.10", "ziel"),
    )
    current = _biofuel_share_value(
        _scoped_renewable_value("4.1.3", "target_value"),
        _scoped_renewable_value("4.1.3.1", "target_value"),
        _scoped_verbrauch_value("2.10", "ziel"),
    )
    return _comparison_row(
        "Anteil Biobrennstoff an Geb.W.",
        status=status,
        basis=basis,
        current=current if current is not None else basis,
        delta_mode="ratio",
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
        _building_renovation_comparison_row(),
        _heat_pump_comparison_row(),
        _solar_thermal_comparison_row(),
        _biofuel_comparison_row(),
        _verbrauch_comparison_row(
            "Wärmeanw.-Effiz.Gewerbe/Industrie",
            "3.2.2",
            delta_mode="ratio",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
        _verbrauch_comparison_row(
            "Syntheseanteil an Grundstoffen",
            "9.1.3",
            delta_mode="ratio",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
        _verbrauch_comparison_row(
            "Anteil Elektrotrakt. Personenverkehr",
            "4.1.1.6",
            delta_mode="ratio",
            scale_max=EFFICIENCY_BAR_SCALE_MAX,
        ),
        _verbrauch_comparison_row(
            "Anteil Elektrotrakt. Güterverkehr",
            "4.1.2.5",
            delta_mode="ratio",
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
            status_code = entry.get("status_code", code)
            target_code = entry.get("target_code", code)
            status.append(_chart_live_value(chart, status_code, status_field))
            basis.append(_chart_snapshot_value(chart, admin_payload, target_code, target_field))
            vor.append(_chart_snapshot_value(chart, vorzustand_payload, target_code, target_field))
            current.append(_chart_live_value(chart, target_code, target_field))

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
        "endenergie_stack_rows": _endenergie_stack_rows(admin_payload, vorzustand_payload),
        "primaerenergie_stack_rows": _primaerenergie_stack_rows(admin_payload, vorzustand_payload),
        "section4_expansion_rows": _section4_expansion_rows(admin_payload, vorzustand_payload),
        "cockpit_energy_bars": _cockpit_energy_bars(),
        "cockpit_effect_rows": _cockpit_effect_rows(),
        "current_section": "modifikationsdetails",
    }
    return render(request, "simulator/modifikationsdetails.html", context)
