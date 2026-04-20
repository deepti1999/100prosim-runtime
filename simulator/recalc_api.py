"""Recalculation and recalc-related HTTP endpoints."""

import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from simulator.models import BalanceJob, CalculationRun
from simulator.recalc_service import recalc_all_renewables_full, run_full_recalc
from simulator.ws_queue_api import _queue_or_reuse_balance_job

logger = logging.getLogger(__name__)
DEPRECATED_RECALC_WS_MESSAGE = (
    "Deprecated endpoint. Use /api/unified-recalc/ for supported WS + renewable recalculation."
)

def run_full_recalc_view(request):
    """
    Explicitly run the heavy cascade once and store a CalculationRun snapshot.
    Intended for the staged “calculate once, read many” flow.
    """
    summary = run_full_recalc()
    run = CalculationRun.objects.create(
        duration_ms=summary["duration_ms"],
        summary=summary,
        triggered_by=request.user.username,
    )
    request.session["latest_run_id"] = run.id
    return JsonResponse(
        {
            "status": "ok",
            "run_id": run.id,
            "duration_ms": run.duration_ms,
            "summary": summary,
            "created_at": run.created_at.isoformat(),
            "landuse_changes": summary.get("landuse_changes", []),  # Include changes for tracking
        }
    )

@login_required
@require_http_methods(["POST"])
def run_renewables_recalc_view(request):
    """
    Queue renewable-only recalculation as a background job to avoid
    request timeouts on Heroku.
    """
    try:
        if settings.DEBUG:
            import time
            start = time.perf_counter()
            renewables_updated = recalc_all_renewables_full(exclude_ws_dependent=False)
            duration_ms = int((time.perf_counter() - start) * 1000)
            summary = {
                "duration_ms": duration_ms,
                "renewables_updated": renewables_updated,
                "scope": "renewables_only",
            }
            run = CalculationRun.objects.create(
                duration_ms=duration_ms,
                summary=summary,
                triggered_by=request.user.username,
            )
            return JsonResponse(
                {
                    "success": True,
                    "queued": False,
                    "status": "succeeded",
                    "run_id": run.id,
                    "duration_ms": duration_ms,
                    "summary": summary,
                    "created_at": run.created_at.isoformat(),
                }
            )

        job = _queue_or_reuse_balance_job(
            request.user,
            BalanceJob.TYPE_RENEWABLES_RECALC,
            {"scope": "renewables_only"},
        )
        return JsonResponse(
            {
                "success": True,
                "queued": True,
                "job_id": str(job.id),
                "status": job.status,
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def recalc_ws_formulas_view(request):
    """
    Refresh WS values from WS 365-day service output.

    DEPRECATED: retained for backward compatibility with old integrations.
    """
    import time
    start = time.time()
    logger.warning(
        "DEPRECATED endpoint called: /api/recalc-ws-formulas/ by user_id=%s path=%s",
        getattr(request.user, "id", None),
        request.path,
    )
    
    try:
        from simulator.ws_365_service import get_ws_365_data

        ws_data = get_ws_365_data(run_goal_seek=False)
        ws_updated = len(ws_data.get("daily_data", []))
        
        duration_ms = int((time.time() - start) * 1000)
        
        response = JsonResponse({
            'status': 'ok',
            'message': f"WS 365 refresh complete! WS days: {ws_updated}",
            'ws_updated': ws_updated,
            'ws_errors': 0,
            'duration_ms': duration_ms,
            'deprecated': True,
            'deprecation_message': DEPRECATED_RECALC_WS_MESSAGE,
        })
        response["X-Deprecated-Endpoint"] = "true"
        return response
    except Exception as e:
        response = JsonResponse({
            'status': 'error',
            'error': str(e),
            'deprecated': True,
            'deprecation_message': DEPRECATED_RECALC_WS_MESSAGE,
        }, status=500)
        response["X-Deprecated-Endpoint"] = "true"
        return response

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def unified_recalc_view(request):
    """
     UNIFIED RECALCULATION WITH OPTIONAL AUTO-BALANCE
    
    This is the RECOMMENDED way to recalculate everything at once.
    
    Order:
    1. Recalculate INPUT renewables (excluding 9.3.1, 9.3.4)
    2. Recalculate WS data
    3. Keep 9.3.1/9.3.4 fixed from DB (no WS -> renewable writes)
    4. (Optional) Auto-balance if balance_after=true
    
    Request body (optional):
    {
        "balance_after": true,      // Auto-balance after recalc (default: true)
        "ws_tolerance": 10.0,       // WS balance tolerance GWh (default: 10.0)
        "energy_tolerance": 1.0,    // Energy balance tolerance GWh (default: 1.0)
        "max_balance_cycles": 6     // Max balance iterations (default: 6)
    }
    
    Result: All values are consistent, system is balanced.
    """
    try:
        # Parse request body for options
        try:
            data = json.loads(request.body or "{}")
        except Exception:
            data = {}
        
        balance_after = data.get('balance_after', True)  # Default: auto-balance
        ws_tolerance = float(data.get('ws_tolerance', 10.0))
        energy_tolerance = float(data.get('energy_tolerance', 1.0))
        max_balance_cycles = int(data.get('max_balance_cycles', 6))
        
        # Import the combined function
        from simulator.recalc_service import unified_recalc_and_balance
        
        # Run unified recalc with optional balance
        stats = unified_recalc_and_balance(
            balance_after=balance_after,
            ws_tolerance=ws_tolerance,
            energy_tolerance=energy_tolerance,
            max_balance_cycles=max_balance_cycles
        )
        
        recalc = stats.get('recalc', {})
        balance = stats.get('balance', {})
        
        # Build response message
        message_parts = [
            f"Input: {recalc.get('input_renewables', 0)}",
            f"WS: {recalc.get('ws_updated', 0)}",
            "Fixed 9.3.1/9.3.4 applied"
        ]
        
        if balance_after:
            if stats.get('is_balanced'):
                message_parts.append(f"Balanced (gap: {balance.get('final_gap', 0):.2f} GWh)")
            else:
                message_parts.append(f"Balance incomplete (gap: {balance.get('final_gap', 0):.2f} GWh)")
        
        return JsonResponse({
            'status': 'ok',
            'message': f"Unified recalc complete! {' | '.join(message_parts)}",
            'input_renewables': recalc.get('input_renewables', 0),
            'ws_updated': recalc.get('ws_updated', 0),
            'output_renewables': recalc.get('output_renewables', 0),
            'duration_ms': stats.get('duration_ms', 0),
            'is_balanced': stats.get('is_balanced', False),
            'balance': balance,
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@csrf_exempt
def recalc_verbrauch_view(request):
    """
    Recalculate all VerbrauchData items.
    Similar to run_full_recalc but only for Verbrauch table.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    
    import time
    start = time.time()
    
    try:
        from simulator.verbrauch_recalculator import recalc_all_verbrauch
        
        # Recalculate all verbrauch items
        updated_codes = recalc_all_verbrauch()
        
        duration_ms = int((time.time() - start) * 1000)
        
        return JsonResponse({
            'status': 'ok',
            'updated': len(updated_codes),
            'duration_ms': duration_ms,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)
