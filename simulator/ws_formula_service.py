"""WS formula compatibility service.

Legacy WSFormulaTemplate execution used WSData row-level columns (including 366/367).
The project now runs WS exclusively via WS 365 calculations.

This module keeps admin/actions backward-compatible without reading/writing legacy
WSData derived columns.
"""

from __future__ import annotations

import re
import time
from typing import Dict, Optional

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

class WSFormulaEvaluator:
    """Compatibility evaluator backed by WS 365 daily/current outputs."""

    def __init__(self):
        self.ws_snapshot: Dict = {}
        self.daily_data = []
        self.current = {}
        self.sums = {}

    def clear_cache(self):
        self.ws_snapshot = {}
        self.daily_data = []
        self.current = {}
        self.sums = {}

    def load_ws_data(self):
        from simulator.ws_365_service import get_ws_365_data

        self.ws_snapshot = get_ws_365_data(run_goal_seek=False) or {}
        self.daily_data = list(self.ws_snapshot.get("daily_data") or [])
        self.current = dict(self.ws_snapshot.get("current") or {})

    def calculate_sums(self):
        self.sums = {
            "sum_einspeich": _safe_float(self.current.get("einspeich_sum")),
            "sum_abregelung_z": _safe_float(self.current.get("abregelung_sum")),
            "sum_ueberschuss_strom": _safe_float(self.current.get("ueberschuss_sum")),
            "sum_ausspeich_rueckverstr": _safe_float(self.current.get("ausspeich_sum")),
            "sum_storage_drift": _safe_float(self.current.get("storage_drift")),
        }

    def _row_dict(self, day: int) -> Dict[str, float]:
        if day < 1 or day > len(self.daily_data):
            return {}
        row = self.daily_data[day - 1] or {}
        if not isinstance(row, dict):
            return {}

        aliases = {
            "stromverbr": "stromverbrauch",
            "stromverbr_raumwaerm_korr": "stromverbr_raumw_korr",
            "solarstrom": "solar_strom",
            "windstrom": "wind_strom",
            "abregelung_z": "abregelung",
            "sonst_kraft_konstant": "sonst_kraftw",
            "ladezust_burtto": "ladezust_brutto",
            "ladezustand_netto": "ladezust_netto",
        }

        out = {}
        for key, value in row.items():
            out[key] = _safe_float(value)
        for old_key, new_key in aliases.items():
            out[old_key] = _safe_float(row.get(new_key))
        return out

    def evaluate_formula(self, formula: str, tag_im_jahr: int, column_name: Optional[str] = None):
        """Best-effort evaluator for admin testing only."""
        del column_name

        if not formula:
            return None

        if not self.daily_data:
            self.load_ws_data()
        if not self.sums:
            self.calculate_sums()

        row = self._row_dict(tag_im_jahr)
        day_prev = self._row_dict(tag_im_jahr - 1)

        expr = formula.replace(";", ",")
        expr = re.sub(r"\bIF\(", "if_fn(", expr)
        expr = re.sub(r"\brow\.", "row_", expr)
        expr = re.sub(r"\bday_prev\.", "day_prev_", expr)

        scope = {
            "__builtins__": {},
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
            "if_fn": lambda cond, t, f: t if cond else f,
            "sums": self.sums,
        }

        for k, v in row.items():
            scope[f"row_{k}"] = _safe_float(v)
        for k, v in day_prev.items():
            scope[f"day_prev_{k}"] = _safe_float(v)

        try:
            value = eval(expr, scope, {})
            return _safe_float(value)
        except Exception:
            return None

_evaluator_instance: Optional[WSFormulaEvaluator] = None

def get_ws_formula_evaluator() -> WSFormulaEvaluator:
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = WSFormulaEvaluator()
    return _evaluator_instance

def recalculate_all_ws_data(preserve_stromverbr=False, num_passes=3) -> Dict[str, int]:
    """Compatibility API: refresh WS 365 outputs and report summary stats."""
    del preserve_stromverbr
    del num_passes

    start = time.perf_counter()
    from simulator.ws_365_service import get_ws_365_data

    ws_data = get_ws_365_data(run_goal_seek=False)
    updated = len(ws_data.get("daily_data", []))
    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "updated": updated,
        "errors": 0,
        "skipped": 0,
        "duration_ms": duration_ms,
    }
