"""Database-driven WS 365 formula engine."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from types import CodeType
from typing import Dict, List, Optional, Tuple

from .models import LandUse, RenewableData, VerbrauchData
from .ws_models import WS365Formula

REQUIRED_DERIVED_COLUMNS: Tuple[str, ...] = (
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
)

@dataclass(frozen=True)
class FormulaSpec:
    column_name: str
    expression: str
    day1_expression: str
    expression_code: Optional[CodeType]
    day1_expression_code: Optional[CodeType]
    stage: str
    order: int

_DAY_PREV_TOKEN_RE = re.compile(r"\bday_prev\.([a-zA-Z_][a-zA-Z0-9_]*)\b")
_COL_MIN_TOKEN_RE = re.compile(r"\bcol_min\.([a-zA-Z_][a-zA-Z0-9_]*)\b")
_COL_MAX_TOKEN_RE = re.compile(r"\bcol_max\.([a-zA-Z_][a-zA-Z0-9_]*)\b")
_COL_SUM_TOKEN_RE = re.compile(r"\bcol_sum\.([a-zA-Z_][a-zA-Z0-9_]*)\b")
_DB_HELPER_NAMES = ("REN_TARGET(", "REN_STATUS(", "VER_ZIEL(", "VER_STATUS(", "LU_TARGET(", "LU_STATUS(")

def _preprocess_expression(expression: str) -> str:
    """Normalize human-friendly shortcuts into evaluator helper calls."""
    expr = (expression or "").strip()
    if not expr:
        return expr

    expr = expr.replace(";", ",")
    expr = _DAY_PREV_TOKEN_RE.sub(r'PREV("\1")', expr)
    expr = _COL_MIN_TOKEN_RE.sub(r'COL_MIN("\1")', expr)
    expr = _COL_MAX_TOKEN_RE.sub(r'COL_MAX("\1")', expr)
    expr = _COL_SUM_TOKEN_RE.sub(r'COL_SUM("\1")', expr)
    return expr

def _to_float_or_zero(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return number

def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator

def _normalize_code(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    return raw.replace("_", ".")

def _build_db_lookup_helpers() -> Dict[str, object]:
    renewable_by_code: Dict[str, RenewableData] = {
        str(row.code): row
        for row in RenewableData.objects.only("code", "status_value", "target_value")
        if row.code
    }
    verbrauch_by_code: Dict[str, VerbrauchData] = {
        str(row.code): row
        for row in VerbrauchData.objects.only("code", "status", "ziel")
        if row.code
    }
    landuse_by_code: Dict[str, LandUse] = {
        str(row.code): row
        for row in LandUse.objects.only("code", "status_ha", "target_ha")
        if row.code
    }

    def ren_target(code: str) -> float:
        row = renewable_by_code.get(_normalize_code(code))
        return _to_float_or_zero(row.target_value if row else 0.0)

    def ren_status(code: str) -> float:
        row = renewable_by_code.get(_normalize_code(code))
        return _to_float_or_zero(row.status_value if row else 0.0)

    def ver_ziel(code: str) -> float:
        row = verbrauch_by_code.get(_normalize_code(code))
        return _to_float_or_zero(row.ziel if row else 0.0)

    def ver_status(code: str) -> float:
        row = verbrauch_by_code.get(_normalize_code(code))
        return _to_float_or_zero(row.status if row else 0.0)

    def lu_target(code: str) -> float:
        lookup_code = str(code or "").strip()
        row = landuse_by_code.get(lookup_code)
        if row is None and not lookup_code.startswith("LU_"):
            row = landuse_by_code.get(f"LU_{lookup_code}")
        return _to_float_or_zero(row.target_ha if row else 0.0)

    def lu_status(code: str) -> float:
        lookup_code = str(code or "").strip()
        row = landuse_by_code.get(lookup_code)
        if row is None and not lookup_code.startswith("LU_"):
            row = landuse_by_code.get(f"LU_{lookup_code}")
        return _to_float_or_zero(row.status_ha if row else 0.0)

    return {
        "REN_TARGET": ren_target,
        "REN_STATUS": ren_status,
        "VER_ZIEL": ver_ziel,
        "VER_STATUS": ver_status,
        "LU_TARGET": lu_target,
        "LU_STATUS": lu_status,
    }

def _compile_expression(expression: str, formula_name: str) -> Optional[CodeType]:
    expr = (expression or "").strip()
    if not expr:
        return None
    try:
        return compile(expr, f"<ws365:{formula_name}>", "eval")
    except SyntaxError as exc:
        raise ValueError(f"WS formula '{formula_name}' has invalid syntax: {exc}") from exc

def _expression_uses_db_helpers(expression: str) -> bool:
    up = (expression or "").upper()
    return any(name in up for name in _DB_HELPER_NAMES)

def _load_active_formulas() -> Tuple[List[FormulaSpec], List[FormulaSpec], bool]:
    formulas = list(
        WS365Formula.objects.filter(is_active=True)
        .only("column_name", "expression", "day1_expression", "stage", "order")
        .order_by("stage", "order", "column_name")
    )
    if not formulas:
        return [], [], False

    daily: List[FormulaSpec] = []
    post: List[FormulaSpec] = []
    uses_db_helpers = False

    for formula in formulas:
        expression = _preprocess_expression(formula.expression)
        day1_expression = _preprocess_expression(formula.day1_expression)
        uses_db_helpers = uses_db_helpers or _expression_uses_db_helpers(expression) or _expression_uses_db_helpers(day1_expression)

        spec = FormulaSpec(
            column_name=formula.column_name,
            expression=expression,
            day1_expression=day1_expression,
            expression_code=_compile_expression(expression, formula.column_name),
            day1_expression_code=_compile_expression(day1_expression, f"{formula.column_name}:day1"),
            stage=formula.stage,
            order=formula.order,
        )
        if formula.stage == WS365Formula.STAGE_POST:
            post.append(spec)
        else:
            daily.append(spec)

    return daily, post, uses_db_helpers

def _evaluate_expression(expression_code: Optional[CodeType], scope: Dict[str, object], formula_name: str) -> float:
    if expression_code is None:
        return 0.0

    try:
        result = eval(expression_code, {"__builtins__": {}}, scope)
    except ZeroDivisionError:
        return 0.0
    except Exception as exc:
        raise ValueError(f"WS formula '{formula_name}' failed: {exc}") from exc
    return _to_float_or_zero(result)

def _run_daily_stage(
    daily_formulas: List[FormulaSpec],
    ws_data: Dict[str, List[float]],
    common_context: Dict[str, float],
    helper_context: Dict[str, object],
) -> Dict[str, List[float]]:
    days = len(ws_data.get("solar_promille") or [])
    columns: Dict[str, List[float]] = {name: [] for name in REQUIRED_DERIVED_COLUMNS}

    for day_idx in range(days):
        row_values: Dict[str, float] = {}
        day_inputs = {
            "solar_promille": _to_float_or_zero(ws_data["solar_promille"][day_idx]),
            "wind_promille": _to_float_or_zero(ws_data["wind_promille"][day_idx]),
            "heizung_abwaerm_promille": _to_float_or_zero(ws_data["heizung_abwaerm_promille"][day_idx]),
            "verbrauch_promille": _to_float_or_zero(ws_data["verbrauch_promille"][day_idx]),
            "day": day_idx + 1,
            "DAY": day_idx + 1,
        }

        def prev(column_name: str) -> float:
            values = columns.get(column_name, [])
            if day_idx <= 0 or not values:
                return 0.0
            return _to_float_or_zero(values[day_idx - 1])

        for formula in daily_formulas:
            expr_code = formula.day1_expression_code if day_idx == 0 and formula.day1_expression_code is not None else formula.expression_code
            if expr_code is None:
                continue

            scope: Dict[str, object] = {
                "IF": lambda cond, a, b: a if cond else b,
                "MIN": min,
                "MAX": max,
                "ABS": abs,
                "ROUND": round,
                "PREV": prev,
                "SAFE_DIV": _safe_div,
                "CLAMP": lambda v, lo, hi: min(max(v, lo), hi),
            }
            scope.update(helper_context)
            scope.update(common_context)
            scope.update(day_inputs)
            scope.update(row_values)

            value = _evaluate_expression(expr_code, scope, formula.column_name)
            row_values[formula.column_name] = value
            columns.setdefault(formula.column_name, []).append(value)

        # Ensure every known output column has the same length.
        for col_name in REQUIRED_DERIVED_COLUMNS:
            if len(columns[col_name]) <= day_idx:
                columns[col_name].append(_to_float_or_zero(row_values.get(col_name)))

    return columns

def _run_post_stage(
    post_formulas: List[FormulaSpec],
    columns: Dict[str, List[float]],
    ws_data: Dict[str, List[float]],
    common_context: Dict[str, float],
    helper_context: Dict[str, object],
) -> Dict[str, List[float]]:
    if not post_formulas:
        return columns

    days = len(ws_data.get("solar_promille") or [])

    def col_min(column_name: str) -> float:
        values = columns.get(column_name, [])
        return min(values) if values else 0.0

    def col_max(column_name: str) -> float:
        values = columns.get(column_name, [])
        return max(values) if values else 0.0

    def col_sum(column_name: str) -> float:
        values = columns.get(column_name, [])
        return float(sum(values)) if values else 0.0

    for formula in post_formulas:
        values = columns.setdefault(formula.column_name, [0.0] * days)
        if len(values) < days:
            values.extend([0.0] * (days - len(values)))

        for day_idx in range(days):
            expr_code = formula.day1_expression_code if day_idx == 0 and formula.day1_expression_code is not None else formula.expression_code
            if expr_code is None:
                continue

            row_values = {name: _to_float_or_zero(vals[day_idx]) for name, vals in columns.items() if len(vals) > day_idx}
            day_inputs = {
                "solar_promille": _to_float_or_zero(ws_data["solar_promille"][day_idx]),
                "wind_promille": _to_float_or_zero(ws_data["wind_promille"][day_idx]),
                "heizung_abwaerm_promille": _to_float_or_zero(ws_data["heizung_abwaerm_promille"][day_idx]),
                "verbrauch_promille": _to_float_or_zero(ws_data["verbrauch_promille"][day_idx]),
                "day": day_idx + 1,
                "DAY": day_idx + 1,
            }

            def prev(column_name: str) -> float:
                col_values = columns.get(column_name, [])
                if day_idx <= 0 or not col_values:
                    return 0.0
                return _to_float_or_zero(col_values[day_idx - 1])

            scope: Dict[str, object] = {
                "IF": lambda cond, a, b: a if cond else b,
                "MIN": min,
                "MAX": max,
                "ABS": abs,
                "ROUND": round,
                "PREV": prev,
                "COL_MIN": col_min,
                "COL_MAX": col_max,
                "COL_SUM": col_sum,
                "SAFE_DIV": _safe_div,
                "CLAMP": lambda v, lo, hi: min(max(v, lo), hi),
            }
            scope.update(helper_context)
            scope.update(common_context)
            scope.update(day_inputs)
            scope.update(row_values)

            values[day_idx] = _evaluate_expression(expr_code, scope, formula.column_name)

    return columns

def calculate_365_days_with_formulas(
    *,
    solar_value: float,
    ws_data: Dict[str, List[float]],
    fixed_values: Dict[str, float],
    grid_loss_rate: float,
    eta_strom_gas: float,
    eta_gas_strom: float,
    wind_value: float | None = None,
) -> Dict[str, object]:
    """
    Execute WS 365 calculations using formulas stored in WS365Formula.

    Raises:
        RuntimeError: if no active formulas exist.
        ValueError: for invalid formula execution.
    """
    daily_formulas, post_formulas, uses_db_helpers = _load_active_formulas()
    if not daily_formulas:
        raise RuntimeError("No active WS365Formula rows found.")

    ziel_911 = _to_float_or_zero(wind_value if wind_value is not None else fixed_values.get("ziel_911"))
    ziel_912 = _to_float_or_zero(solar_value)
    ziel_913 = _to_float_or_zero(fixed_values.get("ziel_913"))
    ziel_914 = _to_float_or_zero(fixed_values.get("ziel_914"))
    ziel_92152 = _to_float_or_zero(fixed_values.get("ziel_92152"))

    annual_demand = _safe_div(_to_float_or_zero(fixed_values.get("verbrauch_7_ziel")), (1 - grid_loss_rate))
    raumw_korr_annual = _to_float_or_zero(fixed_values.get("verbrauch_292_ziel")) * (
        _to_float_or_zero(fixed_values.get("verbrauch_24_ziel")) / 100.0
    )

    sum_renewable = ziel_911 + ziel_912 + ziel_913
    value_after_subtraction = sum_renewable - ziel_92152
    pct = _safe_div(value_after_subtraction, sum_renewable)
    sonst_kraftw_daily = _safe_div(ziel_913 * pct, 365.0)

    common_context = {
        "GRID_LOSS_RATE": _to_float_or_zero(grid_loss_rate),
        "ETA_STROM_GAS": _to_float_or_zero(eta_strom_gas),
        "ETA_GAS_STROM": _to_float_or_zero(eta_gas_strom),
        "annual_demand": annual_demand,
        "raumw_korr_annual": raumw_korr_annual,
        "ziel_911": ziel_911,
        "ziel_912": ziel_912,
        "ziel_913": ziel_913,
        "ziel_914": ziel_914,
        "ziel_92152": ziel_92152,
        "sum_renewable": sum_renewable,
        "value_after_subtraction": value_after_subtraction,
        "pct": pct,
        "sonst_kraftw_daily": sonst_kraftw_daily,
        "brennstoff_factor": 0.0,
    }
    helper_context = _build_db_lookup_helpers() if uses_db_helpers else {}

    pre_columns = _run_daily_stage(daily_formulas, ws_data, common_context, helper_context)
    mangel_last_total = float(sum(pre_columns.get("mangel_last") or []))
    common_context["brennstoff_factor"] = _safe_div(ziel_914, mangel_last_total)

    # Final pass with correct brennstoff_factor.
    columns = _run_daily_stage(daily_formulas, ws_data, common_context, helper_context)
    columns = _run_post_stage(post_formulas, columns, ws_data, common_context, helper_context)

    if not any(f.column_name == "ladezust_abs_vorl_tl" for f in post_formulas):
        lzb = columns.get("ladezust_brutto") or []
        min_lzb = min(lzb) if lzb else 0.0
        columns["ladezust_abs_vorl_tl"] = [v - min_lzb for v in lzb]

    if not any(f.column_name == "ladezust_absolute" for f in post_formulas):
        lzn = columns.get("ladezust_netto") or []
        min_lzn = min(lzn) if lzn else 0.0
        columns["ladezust_absolute"] = [v - min_lzn for v in lzn]

    ordered_derived_columns: List[str] = []
    seen = set()

    for spec in list(daily_formulas) + list(post_formulas):
        key = spec.column_name
        if key not in seen:
            seen.add(key)
            ordered_derived_columns.append(key)

    for key in REQUIRED_DERIVED_COLUMNS:
        if key not in seen:
            seen.add(key)
            ordered_derived_columns.append(key)

    for key in columns.keys():
        if key not in seen:
            seen.add(key)
            ordered_derived_columns.append(key)

    days = len(ws_data.get("solar_promille") or [])
    daily_data: List[Dict[str, float]] = []
    for day_idx in range(days):
        row = {
            "day": day_idx + 1,
            "solar_promille": _to_float_or_zero(ws_data["solar_promille"][day_idx]),
            "wind_promille": _to_float_or_zero(ws_data["wind_promille"][day_idx]),
            "heizung_abwaerm_promille": _to_float_or_zero(ws_data["heizung_abwaerm_promille"][day_idx]),
            "verbrauch_promille": _to_float_or_zero(ws_data["verbrauch_promille"][day_idx]),
        }
        for col_name in ordered_derived_columns:
            values = columns.get(col_name, [])
            value = values[day_idx] if len(values) > day_idx else 0.0
            row[col_name] = round(_to_float_or_zero(value), 2)
        daily_data.append(row)

    ladezust_brutto = columns.get("ladezust_brutto") or [0.0] * days
    einspeich = columns.get("einspeich") or [0.0] * days
    ausspeich_rueckverstr = columns.get("ausspeich_rueckverstr") or [0.0] * days
    abregelung = columns.get("abregelung") or [0.0] * days
    ueberschuss_strom = columns.get("ueberschuss_strom") or [0.0] * days
    solar_strom = columns.get("solar_strom") or [0.0] * days
    wind_strom = columns.get("wind_strom") or [0.0] * days

    base_electricity = ziel_911 + ziel_912 + ziel_913 - ziel_92152
    annual_electricity = (
        base_electricity
        - _safe_div(sum(einspeich), eta_strom_gas)
        - sum(abregelung)
        + ziel_914
        + (sum(ausspeich_rueckverstr) * eta_gas_strom)
    )

    day1_ladezust = ladezust_brutto[0] if ladezust_brutto else 0.0
    day365_ladezust = ladezust_brutto[-1] if ladezust_brutto else 0.0

    return {
        "ladezust_day1": day1_ladezust,
        "ladezust_day365": day365_ladezust,
        "annual_electricity": annual_electricity,
        "annual_demand": annual_demand,
        "storage_drift": day365_ladezust - day1_ladezust,
        "einspeich_sum": sum(einspeich),
        "ausspeich_sum": sum(ausspeich_rueckverstr),
        "abregelung_sum": sum(abregelung),
        "ueberschuss_sum": sum(ueberschuss_strom),
        "solar_strom_sum": sum(solar_strom),
        "wind_strom_sum": sum(wind_strom),
        "renewable_pct": pct * 100.0,
        "daily_data": daily_data,
    }
