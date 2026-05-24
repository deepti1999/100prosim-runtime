"""WS 365 view + WS API endpoints."""

import math

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

WS_INPUT_COLUMNS = [
    "solar_promille",
    "wind_promille",
    "heizung_abwaerm_promille",
    "verbrauch_promille",
]

WS_LEGACY_DERIVED_COLUMNS = [
    "stromverbrauch",
    "davon_raumw_korr",
    "stromverbr_raumw_korr",
    "solar_strom",
    "wind_strom",
    "sonst_kraftw",
    "wind_solar_konstant",
    "direktverbr_strom",
    "ueberschuss_strom",
    "einspeich",
    "abregelung",
    "mangel_last",
    "brennstoff_ausgleich",
    "speicher_ausgl_strom",
    "ausspeich_rueckverstr",
    "ausspeich_gas",
    "ladezust_brutto",
    "ladezust_abs_vorl_tl",
    "selbstentl",
    "ladezust_netto",
    "ladezust_absolute",
]

WS_COLUMN_LABELS = {
    "day": "Tag",
    "solar_promille": "Solar‰",
    "wind_promille": "Wind‰",
    "heizung_abwaerm_promille": "Heiz.‰",
    "verbrauch_promille": "Verbr.‰",
    "stromverbrauch": "Stromverbr.",
    "davon_raumw_korr": "Raumw.korr",
    "stromverbr_raumw_korr": "Verbr.korr",
    "solar_strom": "Solar Strom",
    "wind_strom": "Wind Strom",
    "sonst_kraftw": "Sonst.Kraftw",
    "wind_solar_konstant": "W+S+K",
    "direktverbr_strom": "Direktverbr.",
    "ueberschuss_strom": "Überschuss",
    "einspeich": "Einspeich.",
    "abregelung": "Abregelung",
    "mangel_last": "Mangel-Last",
    "brennstoff_ausgleich": "Brennst.Ausg.",
    "speicher_ausgl_strom": "Speich.Ausg.",
    "ausspeich_rueckverstr": "Ausspeich.R",
    "ausspeich_gas": "Ausspeich.G",
    "ladezust_brutto": "Ladezust.Br.",
    "ladezust_abs_vorl_tl": "Ladezust.Abs.vorl.TL.",
    "selbstentl": "Selbstentl.",
    "ladezust_netto": "Ladezust.Netto",
    "ladezust_absolute": "Ladezust.Absolute",
}

WS_COLUMN_MIN_WIDTH = {
    "day": 50,
    "solar_promille": 80,
    "wind_promille": 80,
    "heizung_abwaerm_promille": 80,
    "verbrauch_promille": 80,
    "ladezust_brutto": 120,
    "ladezust_abs_vorl_tl": 120,
    "ladezust_netto": 120,
    "ladezust_absolute": 120,
}

def _build_ws_summary_context():
    from .ws_365_service import (
        get_ws_365_data,
        calculate_required_landuse,
        get_ws_base_data,
        get_fixed_values,
        goal_seek_optimal_wind,
        calculate_required_landuse_wind,
    )

    data = get_ws_365_data(run_goal_seek=True)

    goal_seek = data.get("goal_seek", {})
    if goal_seek and "optimal_solar" in goal_seek:
        landuse_result = calculate_required_landuse(goal_seek["optimal_solar"])
        goal_seek["required_landuse"] = landuse_result["required_landuse"]
        goal_seek["current_landuse"] = landuse_result["current_landuse"]
        goal_seek["landuse_change"] = landuse_result["landuse_change"]

    ws_data = get_ws_base_data()
    fixed_values = get_fixed_values()
    wind_result = goal_seek_optimal_wind(ws_data, fixed_values)
    wind_landuse = calculate_required_landuse_wind(wind_result["optimal_wind"])
    goal_seek_wind = {
        "optimal_wind": wind_result["optimal_wind"],
        "wind_change": wind_result["wind_change"],
        "wind_change_pct": wind_result["wind_change_pct"],
        "iterations": wind_result["iterations"],
        "storage_drift": wind_result["result"]["storage_drift"],
        "annual_electricity": wind_result["result"]["annual_electricity"],
        "required_landuse": wind_landuse["required_landuse"],
        "current_landuse": wind_landuse["current_landuse"],
        "landuse_change": wind_landuse["landuse_change"],
    }

    return {
        "current": data["current"],
        "goal_seek": goal_seek,
        "goal_seek_wind": goal_seek_wind,
        "daily_data": data.get("daily_data", []),
        "optimal_daily_data": data.get("optimal_daily_data", []),
    }

WS_COLUMN_CLASS = {
    "solar_strom": "text-end text-warning",
    "wind_strom": "text-end text-info",
    "direktverbr_strom": "text-end text-success",
    "einspeich": "text-end text-primary",
    "abregelung": "text-end text-danger",
    "ladezust_brutto": "text-end fw-bold",
    "ladezust_abs_vorl_tl": "text-end fw-bold",
    "ladezust_netto": "text-end fw-bold",
    "ladezust_absolute": "text-end fw-bold",
}

WS_SIGN_COLORED_COLUMNS = {"ladezust_brutto", "ladezust_netto"}

def _to_finite_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number

def _humanize_key(key):
    return str(key or "").replace("_", " ").strip().title()

def _get_ws_derived_columns_from_formulas():
    try:
        from simulator.ws_models import WS365Formula

        keys = list(
            WS365Formula.objects.filter(is_active=True)
            .order_by("stage", "order", "column_name")
            .values_list("column_name", flat=True)
        )
        if keys:
            return keys
    except Exception:
        pass
    return list(WS_LEGACY_DERIVED_COLUMNS)

def _build_ws_columns(daily_data):
    keys = ["day"] + list(WS_INPUT_COLUMNS) + _get_ws_derived_columns_from_formulas()
    seen = set()
    ordered_keys = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        ordered_keys.append(key)

    if daily_data:
        sample = daily_data[0] or {}
        for key in sample.keys():
            if key in seen:
                continue
            seen.add(key)
            ordered_keys.append(key)

    columns = []
    for key in ordered_keys:
        is_day = key == "day"
        columns.append(
            {
                "key": key,
                "label": WS_COLUMN_LABELS.get(key, _humanize_key(key)),
                "is_day": is_day,
                "header_class": "text-center" if is_day else "text-end",
                "cell_class": "text-center fw-bold" if is_day else WS_COLUMN_CLASS.get(key, "text-end"),
                "summary_class": "text-center fw-bold" if is_day else WS_COLUMN_CLASS.get(key, "text-end"),
                "min_width": WS_COLUMN_MIN_WIDTH.get(key, 100),
                "sign_color": key in WS_SIGN_COLORED_COLUMNS,
            }
        )
    return columns

def _compute_ws_daily_min_max(daily_data, fields):
    """
    Build two summary rows (minimum/maximum) across all WS numeric columns.
    """
    min_row = {}
    max_row = {}

    for field in fields:
        values = []
        for row in daily_data or []:
            if isinstance(row, dict):
                raw = row.get(field)
            else:
                raw = getattr(row, field, None)
            num = _to_finite_float(raw)
            if num is not None:
                values.append(num)

        min_row[field] = min(values) if values else None
        max_row[field] = max(values) if values else None

    return min_row, max_row

def _build_ws_row_cells(source_row, ws_columns):
    row = source_row if isinstance(source_row, dict) else {}
    cells = []
    for col in ws_columns:
        value = row.get(col["key"])
        classes = col["cell_class"]
        if col["sign_color"]:
            num = _to_finite_float(value)
            if num is not None:
                classes = f"{classes} {'text-success' if num >= 0 else 'text-danger'}"
        cells.append(
            {
                "is_day": col["is_day"],
                "value": value,
                "classes": classes.strip(),
            }
        )
    return cells

def _build_ws_summary_cells(summary_row, ws_columns, label):
    cells = []
    for col in ws_columns:
        if col["is_day"]:
            cells.append(
                {
                    "is_day": True,
                    "is_label": True,
                    "label": label,
                    "value": None,
                    "classes": col["summary_class"],
                }
            )
            continue

        value = (summary_row or {}).get(col["key"])
        classes = col["summary_class"]
        if col["sign_color"]:
            num = _to_finite_float(value)
            if num is not None:
                classes = f"{classes} {'text-success' if num >= 0 else 'text-danger'}"
        cells.append(
            {
                "is_day": False,
                "is_label": False,
                "label": "",
                "value": value,
                "classes": classes.strip(),
            }
        )
    return cells

@login_required
def ws_view(request):
    """WS 365 Days - Energy Balance Simulation View"""
    summary = _build_ws_summary_context()
    daily_data = summary["daily_data"]
    ws_columns = _build_ws_columns(daily_data)
    ws_fields = [col["key"] for col in ws_columns if not col.get("is_day")]
    ws_min_row, ws_max_row = _compute_ws_daily_min_max(daily_data, ws_fields)
    ws_table_rows = [_build_ws_row_cells(row, ws_columns) for row in daily_data]
    ws_min_cells = _build_ws_summary_cells(ws_min_row, ws_columns, "Min")
    ws_max_cells = _build_ws_summary_cells(ws_max_row, ws_columns, "Max")

    context = {
        'current': summary['current'],
        'goal_seek': summary['goal_seek'],
        'goal_seek_wind': summary['goal_seek_wind'],
        'daily_data': daily_data,
        'ws_columns': ws_columns,
        'ws_table_rows': ws_table_rows,
        'ws_min_cells': ws_min_cells,
        'ws_max_cells': ws_max_cells,
        'ws_min_row': ws_min_row,
        'ws_max_row': ws_max_row,
        'optimal_daily_data': summary.get('optimal_daily_data', []),
        'current_section': 'ws',
    }
    
    return render(request, 'simulator/ws.html', context)

@login_required
def ws_api_data(request):
    """API endpoint to get WS 365 days data as JSON"""
    from .ws_365_service import get_ws_365_data
    
    run_goal_seek = request.GET.get('goal_seek', 'false').lower() == 'true'
    data = get_ws_365_data(run_goal_seek=run_goal_seek)
    
    return JsonResponse(data)

@login_required
def ws_api_summary(request):
    """Return current WS summary cards from the latest DB state."""
    summary = _build_ws_summary_context()
    return JsonResponse({
        "success": True,
        "current": summary["current"],
        "goal_seek": summary["goal_seek"],
        "goal_seek_wind": summary["goal_seek_wind"],
    })

@login_required
def ws_api_goal_seek(request):
    """API endpoint to run Goal Seek and return optimal solar value"""
    from .ws_365_service import get_ws_base_data, get_fixed_values, goal_seek_optimal_solar, calculate_required_landuse
    
    ws_data = get_ws_base_data()
    fixed_values = get_fixed_values()
    result = goal_seek_optimal_solar(ws_data, fixed_values)
    
    landuse_result = calculate_required_landuse(result['optimal_solar'])
    
    return JsonResponse({
        'success': True,
        'original_solar': result['original_solar'],
        'optimal_solar': result['optimal_solar'],
        'solar_change': result['solar_change'],
        'solar_change_pct': result['solar_change_pct'],
        'iterations': result['iterations'],
        'storage_drift': result['result']['storage_drift'],
        'annual_electricity': result['result']['annual_electricity'],
        'annual_demand': result['result']['annual_demand'],
        'required_landuse': landuse_result['required_landuse'],
        'current_landuse': landuse_result['current_landuse'],
        'landuse_change': landuse_result['landuse_change'],
    })
