import math
import time
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from simulator.models import BalanceJob, CalculationRun
from simulator.input_api import _run_verbrauch_recalc_passes
from simulator.owner_scope import owner_scope
from simulator.recalc_service import unified_recalc_all
from simulator.region_scope import region_scope
from simulator.workspace_service import ensure_user_workspace_data
from simulator.recalc_service import recalc_all_renewables_full
from simulator.ws_365_service import (
    apply_balanced_landuse,
    apply_balanced_landuse_sector_first,
    apply_balanced_wind_landuse,
    apply_balanced_wind_landuse_sector_first,
)

def _json_safe(value: Any) -> Any:
    """Convert NaN/Infinity recursively so JSON serialization stays strict."""
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _record_balance_calculation_run(job: BalanceJob, result: Dict[str, Any], duration_ms: int) -> Dict[str, Any]:
    """Create the cache-busting CalculationRun for balance jobs.

    Bilanz/Cockpit cache their computed payload by latest CalculationRun.id.
    WS/sector balance jobs used to mutate LandUse/Renewable/Verbrauch rows
    without creating a CalculationRun, so those pages could keep serving the
    old cached bilanz payload until another recalc happened.
    """
    if result.get("run_id"):
        return result

    summary = {
        "duration_ms": duration_ms,
        "job_type": job.job_type,
        "scope": "balance_job",
        "success": bool(result.get("success")),
        "early_exit": bool(result.get("early_exit")),
    }
    for key in (
        "storage_drift",
        "annual_electricity",
        "landuse_code",
        "old_landuse",
        "new_landuse",
        "old_landuse_percent",
        "new_landuse_percent",
        "sector_balance_ok",
        "drift_ok",
        "overall_balanced",
        "profile",
    ):
        if key in result:
            summary[key] = result.get(key)

    run = CalculationRun.objects.create(
        duration_ms=max(0, int(duration_ms or 0)),
        summary=_json_safe(summary),
        triggered_by=(job.created_by.username if job.created_by else "worker"),
    )
    result = dict(result)
    result.update({
        "run_id": run.id,
        "duration_ms": duration_ms,
        "summary": summary,
        "created_at": run.created_at.isoformat(),
    })
    return result


def run_balance_job(job: BalanceJob) -> Dict[str, Any]:
    """Execute one queued balance job and return JSON-safe result payload."""
    start = time.perf_counter()
    user = job.created_by
    # Phase C (T66): payload carries region_code so the worker (a
    # separate process) runs the dispatch under the user's active
    # region scope instead of always-DE. Pre-Phase-C jobs (or
    # internal callers that didn't stamp it) fall back to DE.
    payload_region_code = (job.payload or {}).get("region_code") or "DE"
    # Staff users can also work in the normal webapp. Those pages are
    # owner-scoped too, so the worker must prepare the same workspace for
    # staff and non-staff users before recalculating dependent values.
    if user:
        ensure_user_workspace_data(user, region_code=payload_region_code)

    # Invalidate ALL process-local caches at entry. Workers process many
    # jobs per lifetime; signals fire in-process only (the web process's
    # save → worker's cache isn't notified). A fresh job must see fresh DB
    # state through all caches or downstream formula evaluations read stale
    # values (observed: user reverts 100→95, worker's auto_tokens_cache
    # still has 1.1.2=100, so formulas compute with old value and say
    # "0 values in 1 pass" — silent no-op bug).
    try:
        from simulator.recalc_cache import invalidate as _invalidate_recalc_cache
        _invalidate_recalc_cache()
    except Exception:
        pass
    try:
        from simulator.formula_service import invalidate_auto_tokens_cache, invalidate_lookups_cache
        invalidate_auto_tokens_cache()
        invalidate_lookups_cache()
    except Exception:
        pass
    try:
        from simulator.ws365_orchestrator import invalidate_ws365_cache
        invalidate_ws365_cache()
    except Exception:
        pass

    with region_scope(payload_region_code), owner_scope(user):
        if job.job_type == BalanceJob.TYPE_SOLAR_SECTOR_WS:
            result = apply_balanced_landuse_sector_first()
        elif job.job_type == BalanceJob.TYPE_WIND_SECTOR_WS:
            result = apply_balanced_wind_landuse_sector_first()
        elif job.job_type == BalanceJob.TYPE_SOLAR_WS_ONLY:
            result = apply_balanced_landuse(
                include_sector_balance=False,
                run_final_renewable_sync=True,
            )
        elif job.job_type == BalanceJob.TYPE_WIND_WS_ONLY:
            # Keep Wind WS-only behavior aligned with Solar WS-only.
            result = apply_balanced_wind_landuse(
                include_sector_balance=False,
                run_final_renewable_sync=True,
            )
        elif job.job_type == BalanceJob.TYPE_RENEWABLES_RECALC:
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
                triggered_by=(user.username if user else "worker"),
            )
            result = {
                "success": True,
                "status": "ok",
                "run_id": run.id,
                "duration_ms": duration_ms,
                "summary": summary,
                "created_at": run.created_at.isoformat(),
            }
        elif job.job_type == BalanceJob.TYPE_VERBRAUCH_RECALC:
            start = time.perf_counter()
            result = _run_verbrauch_recalc_passes(
                triggered_by=(user.username if user else "worker"),
            )
            duration_ms = int((time.perf_counter() - start) * 1000)
            summary = {
                "duration_ms": duration_ms,
                "verbrauch_updated": result["updated_count"],
                "passes": result["passes"],
                "per_pass_updates": result["per_pass_updates"],
                "stabilized": result["stabilized"],
                "scope": "verbrauch_only",
            }
            run = CalculationRun.objects.create(
                duration_ms=duration_ms,
                summary=summary,
                triggered_by=(user.username if user else "worker"),
            )
            result.update({
                "status": "ok",
                "duration_ms": duration_ms,
                "run_id": run.id,
                "summary": summary,
                "created_at": run.created_at.isoformat(),
            })
        elif job.job_type == BalanceJob.TYPE_LANDUSE_RECALC:
            start = time.perf_counter()
            summary = unified_recalc_all()
            duration_ms = int((time.perf_counter() - start) * 1000)
            run_summary = {
                "duration_ms": duration_ms,
                "input_renewables": summary.get("input_renewables", 0),
                "ws365_updated": summary.get("ws365_updated", False),
                "final_renewables": summary.get("final_renewables", 0),
                "scope": "landuse",
            }
            run = CalculationRun.objects.create(
                duration_ms=duration_ms,
                summary=run_summary,
                triggered_by=(user.username if user else "worker"),
            )
            result = {
                "success": True,
                "status": "ok",
                "message": "Land use values saved and recalculated.",
                "duration_ms": duration_ms,
                "run_id": run.id,
                "summary": run_summary,
                "created_at": run.created_at.isoformat(),
            }
        else:
            raise ValueError(f"Unsupported balance job type: {job.job_type}")
    duration_ms = int((time.perf_counter() - start) * 1000)
    result = _record_balance_calculation_run(job, result or {}, duration_ms)
    try:
        from simulator.display_state import invalidate_runtime_caches

        invalidate_runtime_caches()
    except Exception:
        pass
    return _json_safe(result)

def claim_next_job() -> Optional[BalanceJob]:
    """Atomically claim one queued job for processing."""
    with transaction.atomic():
        queued = (
            BalanceJob.objects
            .select_for_update(skip_locked=True)
            .filter(status=BalanceJob.STATUS_QUEUED)
            .order_by("created_at")
            .first()
        )
        if queued is None:
            return None
        queued.status = BalanceJob.STATUS_RUNNING
        queued.started_at = timezone.now()
        queued.attempts = int(queued.attempts or 0) + 1
        queued.error = ""
        queued.save(update_fields=["status", "started_at", "attempts", "error", "updated_at"])
        return queued
