from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from simulator.models import BalanceJob

def _balance_job_timeout_seconds(setting_name, default_seconds):
    """Read timeout values safely from settings with sane minimums."""
    raw = getattr(settings, setting_name, default_seconds)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default_seconds
    return max(60, value)

def _expire_stale_balance_jobs(*, user, job_type):
    """
    Mark stale queued/running jobs as failed so dead worker jobs
    do not block new requests forever.
    """
    now = timezone.now()
    running_cutoff = now - timedelta(
        seconds=_balance_job_timeout_seconds("BALANCE_JOB_RUNNING_TIMEOUT_SECONDS", 20 * 60)
    )
    queued_cutoff = now - timedelta(
        seconds=_balance_job_timeout_seconds("BALANCE_JOB_QUEUED_TIMEOUT_SECONDS", 20 * 60)
    )

    stale_running_message = (
        "Job expired while running. The worker may have restarted. "
        "Please run the action again."
    )
    stale_queued_message = (
        "Job expired in queue. Worker did not pick it up in time. "
        "Please run the action again."
    )

    BalanceJob.objects.filter(
        created_by=user,
        job_type=job_type,
        status=BalanceJob.STATUS_RUNNING,
        started_at__isnull=False,
        started_at__lt=running_cutoff,
    ).update(
        status=BalanceJob.STATUS_FAILED,
        error=stale_running_message,
        finished_at=now,
        updated_at=now,
    )

    BalanceJob.objects.filter(
        created_by=user,
        job_type=job_type,
        status=BalanceJob.STATUS_QUEUED,
        created_at__lt=queued_cutoff,
    ).update(
        status=BalanceJob.STATUS_FAILED,
        error=stale_queued_message,
        finished_at=now,
        updated_at=now,
    )

def _expire_balance_job_if_stale(job):
    """Fail one job in-place when it exceeds queue/running timeout."""
    now = timezone.now()
    running_cutoff = now - timedelta(
        seconds=_balance_job_timeout_seconds("BALANCE_JOB_RUNNING_TIMEOUT_SECONDS", 20 * 60)
    )
    queued_cutoff = now - timedelta(
        seconds=_balance_job_timeout_seconds("BALANCE_JOB_QUEUED_TIMEOUT_SECONDS", 20 * 60)
    )

    if (
        job.status == BalanceJob.STATUS_RUNNING
        and job.started_at
        and job.started_at < running_cutoff
    ):
        job.status = BalanceJob.STATUS_FAILED
        job.error = (
            "Job expired while running. The worker may have restarted. "
            "Please run the action again."
        )
        job.finished_at = now
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
    elif job.status == BalanceJob.STATUS_QUEUED and job.created_at < queued_cutoff:
        job.status = BalanceJob.STATUS_FAILED
        job.error = (
            "Job expired in queue. Worker did not pick it up in time. "
            "Please run the action again."
        )
        job.finished_at = now
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])

def _get_existing_active_balance_job(user, job_type):
    _expire_stale_balance_jobs(user=user, job_type=job_type)
    return (
        BalanceJob.objects
        .filter(
            created_by=user,
            job_type=job_type,
            status__in=[BalanceJob.STATUS_QUEUED, BalanceJob.STATUS_RUNNING],
        )
        .order_by("-created_at")
        .first()
    )

def _active_region_code_from_request(request):
    """Read active_region_code from session, default DE.

    Used to stamp the user's active region into BalanceJob.payload so
    the worker (a separate process) runs the dispatch in the right
    region scope.
    """
    try:
        return (request.session.get("active_region_code") or "DE")
    except AttributeError:
        return "DE"


def _stamp_region(payload, request):
    """Merge the active region into a BalanceJob payload (idempotent)."""
    payload = dict(payload or {})
    payload.setdefault("region_code", _active_region_code_from_request(request))
    return payload


def _queue_or_reuse_balance_job(user, job_type, payload):
    existing_job = _get_existing_active_balance_job(user, job_type)
    if existing_job:
        return existing_job
    return BalanceJob.objects.create(
        job_type=job_type,
        status=BalanceJob.STATUS_QUEUED,
        created_by=user,
        payload=payload or {},
    )

def _queue_new_balance_job(user, job_type, payload):
    """
    Queue a fresh job for data-changing saves.

    Reusing an already-running recalculation job is unsafe after a user edit:
    the old job may have started before the new value was saved, so it would
    finish with stale dependent values. Manual balance buttons can still use
    _queue_or_reuse_balance_job to avoid duplicate heavy jobs.
    """
    _expire_stale_balance_jobs(user=user, job_type=job_type)
    return BalanceJob.objects.create(
        job_type=job_type,
        status=BalanceJob.STATUS_QUEUED,
        created_by=user,
        payload=payload or {},
    )

def _run_balance_job_inline_debug(request, job_type):
    """
    Localhost fallback: execute WS balance job inline when DEBUG is enabled.
    Returns dict result on DEBUG, otherwise None.
    """
    if not settings.DEBUG:
        return None
    from simulator.balance_jobs import run_balance_job
    temp_job = BalanceJob(
        job_type=job_type,
        status=BalanceJob.STATUS_RUNNING,
        created_by=request.user,
        payload=_stamp_region({}, request),
    )
    return run_balance_job(temp_job)

@login_required
def ws_api_apply_balance(request):
    """API endpoint to apply WS-only balance (Solar / LU_2.1)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        inline_result = _run_balance_job_inline_debug(request, BalanceJob.TYPE_SOLAR_WS_ONLY)
        if inline_result is not None:
            return JsonResponse(inline_result)

        job = _queue_or_reuse_balance_job(
            request.user,
            BalanceJob.TYPE_SOLAR_WS_ONLY,
            _stamp_region({}, request),
        )
        return JsonResponse({
            'success': True,
            'queued': True,
            'job_id': str(job.id),
            'status': job.status,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def ws_api_apply_full_balance(request):
    """Queue API endpoint for sector-first + WS/LU rebalance (Solar)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        inline_result = _run_balance_job_inline_debug(request, BalanceJob.TYPE_SOLAR_SECTOR_WS)
        if inline_result is not None:
            return JsonResponse(inline_result)

        job = _queue_or_reuse_balance_job(
            request.user,
            BalanceJob.TYPE_SOLAR_SECTOR_WS,
            _stamp_region({}, request),
        )
        return JsonResponse({
            'success': True,
            'queued': True,
            'job_id': str(job.id),
            'status': job.status,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def ws_api_apply_balance_wind(request):
    """API endpoint to apply WS-only Wind balance (LU_6)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        inline_result = _run_balance_job_inline_debug(request, BalanceJob.TYPE_WIND_WS_ONLY)
        if inline_result is not None:
            return JsonResponse(inline_result)

        job = _queue_or_reuse_balance_job(
            request.user,
            BalanceJob.TYPE_WIND_WS_ONLY,
            _stamp_region({}, request),
        )
        return JsonResponse({
            'success': True,
            'queued': True,
            'job_id': str(job.id),
            'status': job.status,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def ws_api_apply_full_balance_wind(request):
    """Queue API endpoint for sector-first + WS/LU rebalance (Wind)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        inline_result = _run_balance_job_inline_debug(request, BalanceJob.TYPE_WIND_SECTOR_WS)
        if inline_result is not None:
            return JsonResponse(inline_result)

        job = _queue_or_reuse_balance_job(
            request.user,
            BalanceJob.TYPE_WIND_SECTOR_WS,
            _stamp_region({}, request),
        )
        return JsonResponse({
            'success': True,
            'queued': True,
            'job_id': str(job.id),
            'status': job.status,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def ws_api_balance_job_status(request, job_id):
    """Poll endpoint for queued/running/completed balance jobs."""
    try:
        job = BalanceJob.objects.get(id=job_id)
    except BalanceJob.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'}, status=404)

    if job.created_by_id and job.created_by_id != request.user.id and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)

    _expire_balance_job_if_stale(job)

    payload = {
        'success': True,
        'job_id': str(job.id),
        'status': job.status,
        'attempts': job.attempts,
        'error': job.error or '',
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
    }

    if job.status == BalanceJob.STATUS_SUCCEEDED:
        payload['result'] = job.result or {}
    elif job.status in [BalanceJob.STATUS_QUEUED, BalanceJob.STATUS_RUNNING]:
        payload['message'] = 'Balance is still running. Please wait...'

    return JsonResponse(payload)

__all__ = [
    "_queue_new_balance_job",
    "_queue_or_reuse_balance_job",
    "ws_api_apply_balance",
    "ws_api_apply_full_balance",
    "ws_api_apply_balance_wind",
    "ws_api_apply_full_balance_wind",
    "ws_api_balance_job_status",
]
