import math
import time
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from simulator.models import BalanceJob, CalculationRun
from simulator.input_api import _run_verbrauch_recalc_passes
from simulator.owner_scope import owner_scope
from simulator.recalc_service import unified_recalc_all
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

def run_balance_job(job: BalanceJob) -> Dict[str, Any]:
    """Execute one queued balance job and return JSON-safe result payload."""
    user = job.created_by
    if user and not user.is_staff:
        ensure_user_workspace_data(user)

    # Invalidate process-local recalc cache at entry. Workers process many
    # jobs per lifetime; stale cache from a prior job can spuriously match
    # the current signature (hash collisions, state-cycle coincidences) and
    # cause silent no-op recalcs. Fresh job = fresh cache.
    try:
        from simulator.recalc_cache import invalidate as _invalidate_recalc_cache
        _invalidate_recalc_cache()
    except Exception:
        pass

    with owner_scope(user):
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
