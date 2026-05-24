"""Balance core logic and balance HTTP endpoints.

Legacy compatibility layer updated to WS-365-only flows.
No WSData row 366/367 reads/writes are used here.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from calculation_engine.bilanz_engine import calculate_bilanz_data, get_renewable_value
from simulator.models import LandUse
from simulator.signals import compute_ws_diagram_reference, get_ws_constants
from simulator.ws_365_service import (
    apply_balanced_landuse,
    apply_balanced_wind_landuse,
    get_ws_365_data,
)

logger = logging.getLogger(__name__)
DEPRECATED_BALANCE_WS_STORAGE_MESSAGE = (
    "Deprecated endpoint. Use queued WS balance APIs: "
    "/api/ws/apply-balance/ or /api/ws/apply-full-balance/."
)

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

def _driver_to_landuse_code(driver: str) -> str:
    return "LU_6" if driver == "wind" else "LU_2.1"

def _run_ws365_balance(driver: str):
    if driver == "wind":
        return apply_balanced_wind_landuse(
            include_sector_balance=False,
            run_final_renewable_sync=True,
        )
    return apply_balanced_landuse(
        include_sector_balance=False,
        run_final_renewable_sync=True,
    )

def _ws_snapshot():
    ws_data = get_ws_365_data(run_goal_seek=False)
    current = ws_data.get("current", {})
    ws_consts = get_ws_constants()

    drift = _safe_float(current.get("storage_drift"))
    einspeich_sum = _safe_float(current.get("einspeich_sum"))
    abregelung_sum = _safe_float(current.get("abregelung_sum"))
    ausspeich_sum = _safe_float(current.get("ausspeich_sum"))

    eta_strom_gas = _safe_float(ws_consts.get("ETA_STROM_GAS"), 0.65)
    ely_surplus = (einspeich_sum / eta_strom_gas) if eta_strom_gas else 0.0

    diagram = compute_ws_diagram_reference(use_ws_overrides=False)
    reference_stromverbr = _safe_float(diagram.get("stromverbr_raumwaerm_korr_366"))

    return {
        "final_balance": drift,
        "reference_stromverbr": reference_stromverbr,
        "final_stromverbr": reference_stromverbr,
        "abregelung_ws": abregelung_sum,
        "ely_surplus_ws": ely_surplus,
        "ausspeich_sum": ausspeich_sum,
    }

def _balance_ws_storage_core(ws_tolerance=10.0, max_iter=30, num_passes=3, driver="solar"):
    """
    WS-365-only storage balance.

    Runs modern WS balance flow, then returns compatibility fields
    previously exposed by legacy /api/ws/balance/ endpoints.
    """
    del max_iter
    del num_passes

    _run_ws365_balance(driver)
    snapshot = _ws_snapshot()
    final_balance = snapshot["final_balance"]

    return {
        "is_balanced": abs(final_balance) <= float(ws_tolerance),
        "final_balance": final_balance,
        "final_stromverbr": snapshot["final_stromverbr"],
        "reference_stromverbr": snapshot["reference_stromverbr"],
        "abregelung_ws": snapshot["abregelung_ws"],
        "ely_surplus_ws": snapshot["ely_surplus_ws"],
        "iterations": 0,
    }

def _balance_energy_core(driver="solar", energy_tolerance=1.0, max_iter=20, num_passes=1):
    """
    Energy balance via WS-365 orchestrator (no WSData row-level operations).
    """
    del max_iter
    del num_passes

    driver = (driver or "solar").lower()
    landuse_code = _driver_to_landuse_code(driver)

    try:
        lu = LandUse.objects.get(code=landuse_code)
    except LandUse.DoesNotExist:
        return {"is_balanced": False, "error": f"LandUse {landuse_code} not found"}

    old_ha = _safe_float(lu.target_ha)
    result = _run_ws365_balance(driver)

    bilanz = calculate_bilanz_data()
    demand = _safe_float(bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0))
    renewable = _safe_float(get_renewable_value("10.1", use_target=True, fail_fast=False) or 0)
    gap = demand - renewable

    lu.refresh_from_db()
    final_ha = _safe_float(lu.target_ha)

    return {
        "is_balanced": abs(gap) <= float(energy_tolerance),
        "initial_gap": None,
        "final_gap": gap,
        "initial_ha": old_ha,
        "final_ha": final_ha,
        "demand": demand,
        "renewable": renewable,
        "driver": landuse_code,
        "iterations": _safe_float(result.get("iterations", 0)),
    }

def _balance_energy_lu6_core(energy_tolerance=1.0, max_iter=20, num_passes=1):
    return _balance_energy_core(
        driver="wind",
        energy_tolerance=energy_tolerance,
        max_iter=max_iter,
        num_passes=num_passes,
    )

def perform_ws_balance(max_iter: int = 30, tol: float = 10.0, driver: str = "solar"):
    """Compatibility helper returning legacy WS payload keys."""
    result = _balance_ws_storage_core(ws_tolerance=tol, max_iter=max_iter, driver=driver)
    ws_consts = get_ws_constants()

    eta_strom_gas = _safe_float(ws_consts.get("ETA_STROM_GAS"), 0.65)
    eta_gas_strom = _safe_float(ws_consts.get("ETA_GAS_STROM"), 0.585)

    h2_surplus_ws = result.get("ely_surplus_ws", 0) * eta_strom_gas
    gas_storage_ws = h2_surplus_ws
    t_value_ws = _safe_float(_ws_snapshot().get("ausspeich_sum", 0)) * eta_gas_strom

    return {
        "reference_stromverbr": result.get("reference_stromverbr", 0),
        "final_stromverbr": result.get("final_stromverbr", 0),
        "storage_drift": result.get("final_balance", 0),
        "abregelung_ws": result.get("abregelung_ws", 0),
        "ely_surplus_ws": result.get("ely_surplus_ws", 0),
        "h2_surplus_ws": h2_surplus_ws,
        "gas_storage_ws": gas_storage_ws,
        "t_value_ws": t_value_ws,
    }

def perform_energy_balance(driver: str = "solar", tolerance: float = 1.0):
    """Compatibility helper for energy balancing payload."""
    return _balance_energy_core(driver=driver, energy_tolerance=tolerance)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_full_system(request):
    """
    Legacy endpoint maintained for compatibility.
    Uses WS-365 orchestrator and reports combined energy + storage state.
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    driver = (data.get("driver") or "solar").lower()
    ws_tolerance = float(data.get("ws_tolerance", 10.0))
    energy_tolerance = float(data.get("energy_tolerance", 1.0))

    energy_result = _balance_energy_core(driver=driver, energy_tolerance=energy_tolerance)
    if energy_result.get("error"):
        return JsonResponse({"status": "error", "message": energy_result["error"]}, status=400)

    ws_result = _balance_ws_storage_core(ws_tolerance=ws_tolerance, driver=driver)
    is_balanced = bool(energy_result.get("is_balanced") and ws_result.get("is_balanced"))

    return JsonResponse({
        "status": "fully_balanced" if is_balanced else "partial",
        "message": "System balanced" if is_balanced else "System converged with residual gap",
        "total_iterations": 1,
        "ws_result": {
            "is_balanced": ws_result.get("is_balanced", False),
            "final_balance": ws_result.get("final_balance", 0),
            "final_stromverbr": ws_result.get("final_stromverbr", 0),
        },
        "energy_result": {
            "is_balanced": energy_result.get("is_balanced", False),
            "final_gap": energy_result.get("final_gap", 0),
            "final_ha": energy_result.get("final_ha", 0),
            "demand": energy_result.get("demand", 0),
            "renewable": energy_result.get("renewable", 0),
        },
        "iteration_history": [
            {
                "iteration": 1,
                "ws_balanced": ws_result.get("is_balanced", False),
                "ws_balance_value": round(_safe_float(ws_result.get("final_balance", 0)), 2),
                "energy_balanced": energy_result.get("is_balanced", False),
                "energy_gap": round(_safe_float(energy_result.get("final_gap", 0)), 2),
            }
        ],
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_all(request):
    """
    Legacy endpoint for compatibility with old clients.
    Internally delegates to modern WS-365 balance flow.
    """
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    driver = (data.get("driver") or "solar").lower()
    tolerance = float(data.get("tolerance", 1.0))
    ws_tolerance = float(data.get("ws_tolerance", 10.0))

    energy_result = _balance_energy_core(driver=driver, energy_tolerance=tolerance)
    if energy_result.get("error"):
        return JsonResponse({"status": "error", "message": energy_result["error"]}, status=400)

    ws_result = _balance_ws_storage_core(ws_tolerance=ws_tolerance, driver=driver)

    return JsonResponse({
        "status": "ok",
        "overall_status": "balanced" if (energy_result.get("is_balanced") and ws_result.get("is_balanced")) else "partial",
        "iterations": 1,
        "gap_after_ws": energy_result.get("final_gap", 0),
        "ws": {
            "final_stromverbr": ws_result.get("final_stromverbr", 0),
            "storage_drift": ws_result.get("final_balance", 0),
            "abregelung_ws": ws_result.get("abregelung_ws", 0),
            "ely_surplus_ws": ws_result.get("ely_surplus_ws", 0),
            "is_balanced": ws_result.get("is_balanced", False),
        },
        "energy": {
            "final_ha": energy_result.get("final_ha", 0),
            "final_gap": energy_result.get("final_gap", 0),
            "demand": energy_result.get("demand", 0),
            "renewable": energy_result.get("renewable", 0),
            "is_balanced": energy_result.get("is_balanced", False),
        },
        "cycles": [
            {
                "iteration": 1,
                "gap_after_ws": energy_result.get("final_gap", 0),
                "ws_ladezustand": ws_result.get("final_balance", 0),
                "stromverbr": ws_result.get("final_stromverbr", 0),
                "landuse_target_ha": energy_result.get("final_ha", 0),
            }
        ],
    })

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_ws_storage(request):
    """
    Deprecated compatibility endpoint.
    """
    logger.warning(
        "DEPRECATED endpoint called: /api/ws/balance/ by user_id=%s path=%s",
        getattr(request.user, "id", None),
        request.path,
    )

    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    driver = (data.get("driver") or "solar").lower()

    result = _balance_ws_storage_core(driver=driver)
    ws_consts = get_ws_constants()

    eta_strom_gas = _safe_float(ws_consts.get("ETA_STROM_GAS"), 0.65)
    eta_gas_strom = _safe_float(ws_consts.get("ETA_GAS_STROM"), 0.585)

    h2_surplus_ws = result.get("ely_surplus_ws", 0) * eta_strom_gas
    gas_storage_ws = h2_surplus_ws
    t_value_ws = _safe_float(_ws_snapshot().get("ausspeich_sum", 0)) * eta_gas_strom

    response = JsonResponse({
        "status": "balanced" if result["is_balanced"] else "converged_with_residual",
        "message": (
            f"Storage drift = {result['final_balance']:.2f} GWh (target: 0)"
            if not result["is_balanced"]
            else "Balanced successfully"
        ),
        "reference_stromverbr": result.get("reference_stromverbr", 0),
        "final_stromverbr": result.get("final_stromverbr", 0),
        "storage_drift": result.get("final_balance", 0),
        "is_balanced": result["is_balanced"],
        "abregelung_ws": result.get("abregelung_ws", 0),
        "ely_surplus_ws": result.get("ely_surplus_ws", 0),
        "h2_surplus_ws": h2_surplus_ws,
        "gas_storage_ws": gas_storage_ws,
        "t_value_ws": t_value_ws,
        "iterations": result.get("iterations", 0),
        "deprecated": True,
        "deprecation_message": DEPRECATED_BALANCE_WS_STORAGE_MESSAGE,
    })
    response["X-Deprecated-Endpoint"] = "true"
    return response

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_energy(request):
    """Compatibility endpoint for energy balancing."""
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    driver = (data.get("driver") or "solar").lower()
    tolerance = float(data.get("tolerance", 1.0))

    result = _balance_energy_core(driver=driver, energy_tolerance=tolerance)
    if result.get("error"):
        return JsonResponse({"status": "error", "message": result["error"]}, status=400)

    landuse_code = result.get("driver", _driver_to_landuse_code(driver))
    try:
        lu = LandUse.objects.select_related("parent").get(code=landuse_code)
    except LandUse.DoesNotExist:
        lu = None

    if lu is not None:
        old_ha = _safe_float(result.get("initial_ha", lu.target_ha or 0))
        new_ha = _safe_float(lu.target_ha)
        old_percent = (
            (old_ha / float(lu.parent.target_ha)) * 100.0
            if lu.parent and lu.parent.target_ha
            else 0.0
        )
        new_percent = (
            (new_ha / float(lu.parent.target_ha)) * 100.0
            if lu.parent and lu.parent.target_ha
            else 0.0
        )
        landuse_change = {
            "code": lu.code,
            "name": lu.name,
            "old_percent": round(old_percent, 2),
            "new_percent": round(new_percent, 2),
            "old_ha": round(old_ha, 2),
            "new_ha": round(new_ha, 2),
            "change_ha": round(new_ha - old_ha, 2),
            "source": f"balance_{driver}",
        }
    else:
        landuse_change = None

    summary = {
        "status": "balanced" if result.get("is_balanced") else "partial",
        "initial_gap": result.get("initial_gap", result.get("final_gap", 0)),
        "final_gap": result.get("final_gap", 0),
        "initial_ha": result.get("initial_ha", result.get("final_ha", 0)),
        "final_ha": result.get("final_ha", 0),
        "demand": result.get("demand", 0),
        "renewable": result.get("renewable", 0),
        "driver": result.get("driver", landuse_code),
        "landuse_change": landuse_change,
    }
    return JsonResponse({"status": "ok", "summary": summary})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def balance_energy_lu6(request):
    """Compatibility endpoint for LU_6 wind balancing."""
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}

    tolerance = float(data.get("tolerance", 1.0))
    result = _balance_energy_lu6_core(energy_tolerance=tolerance)
    if result.get("error"):
        return JsonResponse({"status": "error", "message": result["error"]}, status=400)

    try:
        lu = LandUse.objects.select_related("parent").get(code="LU_6")
        old_ha = _safe_float(result.get("initial_ha", lu.target_ha or 0))
        new_ha = _safe_float(lu.target_ha)
        old_percent = (
            (old_ha / float(lu.parent.target_ha)) * 100.0
            if lu.parent and lu.parent.target_ha
            else 0.0
        )
        new_percent = (
            (new_ha / float(lu.parent.target_ha)) * 100.0
            if lu.parent and lu.parent.target_ha
            else 0.0
        )
        landuse_change = {
            "code": lu.code,
            "name": lu.name,
            "old_percent": round(old_percent, 2),
            "new_percent": round(new_percent, 2),
            "old_ha": round(old_ha, 2),
            "new_ha": round(new_ha, 2),
            "change_ha": round(new_ha - old_ha, 2),
            "source": "balance_lu6",
        }
    except LandUse.DoesNotExist:
        landuse_change = None

    summary = {
        "status": "balanced" if result.get("is_balanced") else "partial",
        "initial_gap": result.get("initial_gap", result.get("final_gap", 0)),
        "final_gap": result.get("final_gap", 0),
        "initial_ha": result.get("initial_ha", result.get("final_ha", 0)),
        "final_ha": result.get("final_ha", 0),
        "demand": result.get("demand", 0),
        "renewable": result.get("renewable", 0),
        "driver": result.get("driver", "LU_6"),
        "landuse_change": landuse_change,
    }
    return JsonResponse({"status": "ok", "summary": summary})
