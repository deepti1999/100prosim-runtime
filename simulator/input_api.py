import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from simulator.admin_roles import user_can_edit_workspace_values
from simulator.display_state import mark_display_state_changed
from simulator.verbrauch_recalculator import recalc_all_verbrauch
from .models import LandUse, ModificationHistoryEntry, RenewableData, VerbrauchData


def _log_modification(*, user, model_label, code, field, before, after, source="user"):
    """Phase 6-A (T61): append-only log of user-initiated modifications.

    Wraps in try/except so logging failures never break the underlying
    save. We only log from the API endpoints (this module) so cascade-
    driven saves don't spam the log.
    """
    try:
        ModificationHistoryEntry.objects.create(
            owner=user if (user is not None and user.is_authenticated) else None,
            model_label=model_label,
            code=code or "",
            field=field,
            value_before=before,
            value_after=after,
            source=source,
        )
    except Exception:
        pass

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

def _run_verbrauch_recalc_passes(*, triggered_by="unknown"):
    """Run the existing multi-pass Verbrauch recalculation until it stabilizes.

    Invalidates the recalc cache at entry because the worker's process-local
    cache can contain stale signatures from prior jobs. The outer multi-pass
    loop below MUST see fresh state each pass; short-circuiting via a cached
    no-change result causes "Recalculated 0 values in 1 pass" silent-no-op
    bugs (observed when user reverts a Verbrauch value back to a prior
    user_percent — the downstream cascade doesn't revert because pass 1
    returns the cached empty result)."""
    from simulator.recalc_cache import invalidate as _invalidate_recalc_cache
    _invalidate_recalc_cache()

    max_passes = 12
    per_pass_updates = []
    unique_codes = set()

    for pass_no in range(1, max_passes + 1):
        updated_codes = recalc_all_verbrauch(
            trigger_code=f"save_recalc_pass_{pass_no}",
        )
        per_pass_updates.append(len(updated_codes))
        unique_codes.update(updated_codes)
        if not updated_codes:
            break

    pass_count = len(per_pass_updates)
    stabilized = (per_pass_updates[-1] == 0) if per_pass_updates else True
    message = (
        f"Recalculated {len(unique_codes)} values in {pass_count} pass(es)"
        + ("" if stabilized else " (max passes reached)")
    )

    return {
        'success': True,
        'message': message,
        'updated_count': len(unique_codes),
        'passes': pass_count,
        'per_pass_updates': per_pass_updates,
        'stabilized': stabilized,
        'triggered_by': triggered_by,
    }

def _get_landuse_current_percent(landuse):
    """
    Current editable percent shown to user.
    Priority: user_percent -> target share -> 0.
    """
    if landuse.user_percent is not None:
        return float(landuse.user_percent)

    if landuse.parent and landuse.parent.target_ha and landuse.target_ha is not None:
        parent_target = float(landuse.parent.target_ha or 0)
        if parent_target > 0:
            return float(landuse.target_ha) / parent_target * 100.0

    return 0.0

def _get_landuse_baseline_percent(landuse):
    """
    Immutable baseline for max-increase validation.
    If stored baseline exists, use it; otherwise fallback to current percent.
    """
    if getattr(landuse, 'increase_limit_baseline_percent', None) is not None:
        return float(landuse.increase_limit_baseline_percent)

    return _get_landuse_current_percent(landuse)

def _ensure_landuse_baseline_percent(landuse):
    """
    Persist baseline once from current percent so repeated +3 edits cannot bypass the cap.
    """
    baseline = _get_landuse_baseline_percent(landuse)
    if getattr(landuse, 'increase_limit_baseline_percent', None) is None:
        landuse.increase_limit_baseline_percent = baseline
        # Save only baseline metadata; avoid heavy cascades.
        landuse.save(update_fields=['increase_limit_baseline_percent'], skip_cascade=True)
    return float(baseline)

def _check_landuse_increase_limit(landuse, requested_percent):
    """
    Enforce absolute increase cap from baseline (not from last edited value).
    Returns (is_valid, details_dict).
    """
    max_increase_points = float(getattr(settings, 'LANDUSE_MAX_INCREASE_PERCENT', 3))
    baseline_percent = _ensure_landuse_baseline_percent(landuse)
    current_percent = _get_landuse_current_percent(landuse)
    max_allowed_value = baseline_percent + max_increase_points
    increase_from_baseline = requested_percent - baseline_percent

    is_valid = increase_from_baseline <= (max_increase_points + 1e-9)
    return is_valid, {
        'max_increase_points': max_increase_points,
        'baseline_percent': baseline_percent,
        'current_percent': current_percent,
        'requested_percent': requested_percent,
        'increase_from_baseline': increase_from_baseline,
        'max_allowed_value': max_allowed_value,
    }


def _resolve_landuse_for_update_pk(pk):
    """
    Resolve the row edited by the UI.

    Older callers/tests may still post the global/base row pk. In the normal
    webapp, authenticated users edit their own workspace copy, so map that pk
    back to the visible scoped row by stable code + region.
    """
    scoped_qs = LandUse.objects.select_related("parent")
    try:
        return scoped_qs.get(pk=pk)
    except LandUse.DoesNotExist:
        source = get_object_or_404(LandUse.all_objects.select_related("region"), pk=pk)
        lookup = {"code": source.code}
        if getattr(source, "region_id", None):
            lookup["region_id"] = source.region_id
        else:
            lookup["region__isnull"] = True
        return get_object_or_404(scoped_qs, **lookup)


@require_http_methods(["POST"])
def save_and_recalculate_verbrauch(request):
    """Queue Verbrauch recalculation on hosted environments; keep inline fallback locally."""
    try:
        host = request.get_host() if hasattr(request, "get_host") else ""
        if settings.DEBUG or host.startswith("testserver"):
            payload = _run_verbrauch_recalc_passes(
                triggered_by=getattr(request.user, "username", "debug"),
            )
            run = mark_display_state_changed(
                scope="verbrauch_recalc_inline",
                triggered_by=getattr(request.user, "username", "debug"),
                duration_ms=0,
                updated_count=payload.get("updated_count", 0),
                passes=payload.get("passes", 0),
            )
            payload["run_id"] = run.id
            return JsonResponse(payload)

        from simulator.models import BalanceJob
        from simulator.ws_queue_api import _queue_new_balance_job, _stamp_region

        job = _queue_new_balance_job(
            getattr(request, "user", None),
            BalanceJob.TYPE_VERBRAUCH_RECALC,
            _stamp_region({"scope": "verbrauch"}, request),
        )
        return JsonResponse({
            'success': True,
            'queued': True,
            'job_id': str(job.id),
            'status': job.status,
            'message': 'Verbrauch recalculation queued.',
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@csrf_exempt
@login_required
def update_landuse_percent(request, pk):
    """
    Update the user_percent of a LandUse item and recalc target_ha automatically.
    FIXED: Uses model save() to trigger signals for auto-cascade.

    VALIDATION: Prevents excessive increases to maintain realistic land use changes.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=400)
    if not user_can_edit_workspace_values(request.user):
        return JsonResponse(
            {"status": "error", "message": "Keine Berechtigung zum Bearbeiten von Werten."},
            status=403,
        )

    try:
        data = json.loads(request.body)
        new_percent = float(data.get("user_percent"))

        if new_percent < 0 or new_percent > 100:
            return JsonResponse({
                "status": "error",
                "message": "Percentage must be between 0 and 100"
            }, status=400)

    except (ValueError, TypeError):
        return JsonResponse({
            "status": "error",
            "message": "Invalid percentage value"
        }, status=400)
    except Exception:
        return JsonResponse({
            "status": "error",
            "message": "Invalid request data"
        }, status=400)

    try:
        landuse = _resolve_landuse_for_update_pk(pk)

        if not landuse.parent:
            return JsonResponse({
                "status": "error",
                "message": "Cannot update root level land use"
            }, status=400)

        is_valid, details = _check_landuse_increase_limit(landuse, new_percent)
        if not is_valid:
            return JsonResponse({
                "status": "error",
                "message": f"Cannot increase land use by more than {details['max_increase_points']:.0f} percentage points from baseline.\n\n"
                          f"Baseline (Status): {details['baseline_percent']:.2f}%\n"
                          f"Current Input: {details['current_percent']:.2f}%\n"
                          f"Requested: {details['requested_percent']:.2f}%\n"
                          f"Increase from baseline: {details['increase_from_baseline']:.2f} percentage points\n"
                          f"Maximum allowed: {details['max_allowed_value']:.2f}%\n\n"
                          f"Please stay within the allowed range.",
                "current_value": float(details['current_percent']),
                "baseline_value": float(details['baseline_percent']),
                "max_allowed_value": float(details['max_allowed_value']),
                "max_increase_percent": float(details['max_increase_points'])
            }, status=400)

        if landuse.target_locked:
            landuse.target_locked = False

        old_target_ha = landuse.target_ha
        old_percent = _get_landuse_current_percent(landuse)

        parent_target = landuse.parent.target_ha or 0
        new_target_ha = (parent_target * new_percent) / 100.0

        landuse.user_percent = new_percent
        landuse.target_ha = new_target_ha
        landuse.save()
        mark_display_state_changed(
            scope="landuse_user_percent",
            triggered_by=getattr(request.user, "username", "unknown"),
            code=landuse.code,
        )

        target_percent = (new_target_ha / parent_target * 100) if parent_target else 0
        change_ha = new_target_ha - (old_target_ha or 0)

        return JsonResponse({
            "status": "ok",
            "code": landuse.code,
            "name": landuse.name,
            "new_target_ha": float(new_target_ha),
            "new_target_percent": float(target_percent),
            "old_target_ha": float(old_target_ha) if old_target_ha else None,
            "change_ha": float(change_ha),
            "message": f"Updated {landuse.code} to {new_percent}% - renewables auto-updated",
            "change": {
                "code": landuse.code,
                "name": landuse.name,
                "old_percent": float(old_percent) if old_percent else None,
                "new_percent": float(new_percent),
                "old_ha": float(old_target_ha) if old_target_ha else None,
                "new_ha": float(new_target_ha),
                "change_ha": float(change_ha)
            }
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to update: {str(e)}"
        }, status=500)

def update_verbrauch_bulk(request):
    """
    Update user_percent for multiple VerbrauchData items in bulk.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)
    if not user_can_edit_workspace_values(request.user):
        return JsonResponse(
            {'status': 'error', 'error': 'Keine Berechtigung zum Bearbeiten von Werten.'},
            status=403,
        )

    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])

        updated_count = 0
        recalc_job_id = None
        for update in updates:
            code = update.get('code')
            user_percent = update.get('user_percent')

            if code and user_percent is not None:
                try:
                    item = VerbrauchData.objects.get(code=code)
                    item.user_percent = float(user_percent)
                    item.save(skip_cascade=True, skip_verbrauch_recalc=True)
                    updated_count += 1
                except VerbrauchData.DoesNotExist:
                    pass

        if updated_count:
            mark_display_state_changed(
                scope="verbrauch_bulk_user_percent",
                triggered_by=getattr(request.user, "username", "unknown"),
                updated_count=updated_count,
            )
            try:
                from simulator.models import BalanceJob
                from simulator.ws_queue_api import _queue_new_balance_job, _stamp_region

                recalc_job = _queue_new_balance_job(
                    request.user,
                    BalanceJob.TYPE_VERBRAUCH_RECALC,
                    _stamp_region({"scope": "verbrauch", "trigger_code": "bulk"}, request),
                )
                recalc_job_id = str(recalc_job.id) if recalc_job else None
            except Exception as e:
                print(f"Failed to enqueue verbrauch_recalc after bulk save: {e}")

        return JsonResponse({
            'status': 'ok',
            'updated': updated_count,
            'recalc_job_id': recalc_job_id,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_verbrauch_user_input(request):
    """
    Save user input for a single Verbrauch item and trigger recalculation.
    Similar to land use: saves value, applies it, and recalculates everything.

    Returns which percentage siblings were auto-rebalanced for UI highlighting.
    """
    if not user_can_edit_workspace_values(request.user):
        return JsonResponse(
            {'success': False, 'error': 'Keine Berechtigung zum Bearbeiten von Werten.'},
            status=403,
        )

    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_percent = data.get('user_percent')

        if not code:
            return JsonResponse({'success': False, 'error': 'Missing code'}, status=400)

        try:
            item = VerbrauchData.objects.get(code=code)
        except VerbrauchData.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Verbrauch code {code} not found'}, status=404)

        old_value = item.user_percent
        item.user_percent = float(user_percent) if user_percent is not None else None
        # Keep per-cell saves responsive. The queued worker job below performs
        # the full Verbrauch cascade before the page reloads.
        item.save(skip_cascade=True, skip_verbrauch_recalc=True)

        recalc_job_id = None
        try:
            from simulator.models import BalanceJob
            from simulator.ws_queue_api import _queue_new_balance_job, _stamp_region
            recalc_job = _queue_new_balance_job(
                request.user,
                BalanceJob.TYPE_VERBRAUCH_RECALC,
                _stamp_region({"scope": "verbrauch", "trigger_code": code}, request),
            )
            recalc_job_id = str(recalc_job.id) if recalc_job else None
        except Exception as e:
            print(f"Failed to enqueue verbrauch_recalc after per-cell save: {e}")

        # Phase 6-A (T61): log user-initiated modification.
        _log_modification(
            user=request.user,
            model_label="VerbrauchData",
            code=code,
            field="user_percent",
            before=old_value,
            after=item.user_percent,
            source="user",
        )

        rebalanced = {}
        try:
            from simulator.percentage_rebalancer import get_percentage_group
            group = get_percentage_group(code)
            if group and item.unit == '%':
                for member_code in group['member_codes']:
                    try:
                        member = VerbrauchData.objects.get(code=member_code)
                        rebalanced[member_code] = {
                            'new': member.ziel,
                            'user_percent': member.user_percent,
                            'is_primary': member_code == code
                        }
                    except VerbrauchData.DoesNotExist:
                        pass
        except Exception as e:
            print(f"Error getting rebalance info: {e}")

        return JsonResponse({
            'success': True,
            'code': code,
            'old_value': old_value,
            'new_value': item.user_percent,
            'message': f'Updated {code} user input to {user_percent}%',
            'rebalanced': rebalanced,
            'recalc_job_id': recalc_job_id,
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid value: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_renewable_user_input(request):
    """
    Save one renewable user input and mirror it to target value for frontend-editable rows.
    """
    if not user_can_edit_workspace_values(request.user):
        return JsonResponse(
            {'success': False, 'error': 'Keine Berechtigung zum Bearbeiten von Werten.'},
            status=403,
        )

    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_input = data.get('user_input')

        if not code:
            return JsonResponse({'success': False, 'error': 'Missing code'}, status=400)

        try:
            item = RenewableData.objects.get(code=code)
        except RenewableData.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Renewable code {code} not found'}, status=404)

        if not item.is_fixed or not item.user_editable:
            return JsonResponse(
                {'success': False, 'error': f'Code {code} is not enabled for user editing'},
                status=400,
            )

        if user_input in ('', None):
            return JsonResponse({'success': False, 'error': 'Missing user input value'}, status=400)

        numeric_value = float(user_input)
        old_value = item.user_input
        item.user_input = numeric_value
        # Phase 4-E (T25): fire cascade so dependent cells recompute
        # automatically — the Excel behaviour stakeholders expect per
        # PDF §2.4.4. This is cascade propagation, NOT a Balance run.
        item.save()

        # Re-read after save so target_value reflects any cascade-updated state.
        item.refresh_from_db()
        mark_display_state_changed(
            scope="renewable_user_input",
            triggered_by=getattr(request.user, "username", "unknown"),
            code=code,
        )

        # Phase 6-A (T61): log user-initiated modification.
        _log_modification(
            user=request.user,
            model_label="RenewableData",
            code=code,
            field="user_input",
            before=old_value,
            after=item.user_input,
            source="user",
        )

        return JsonResponse({
            'success': True,
            'code': code,
            'old_value': old_value,
            'user_input': item.user_input,
            'target_value': item.target_value,
            'message': f'Updated {code} user input to {numeric_value}',
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid value: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

__all__ = [
    "_get_landuse_current_percent",
    "_get_landuse_baseline_percent",
    "_ensure_landuse_baseline_percent",
    "_check_landuse_increase_limit",
    "save_and_recalculate_verbrauch",
    "update_landuse_percent",
    "update_verbrauch_bulk",
    "save_verbrauch_user_input",
    "save_renewable_user_input",
]
