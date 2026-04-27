"""
Reset testsim's per-user workspace data to a known-good snapshot dumped
from another stack's testsim. Bypasses model.save() (uses QuerySet.update)
so it does NOT trigger cascades / signals.

Usage inside a container (Django context already set up):
    python manage.py shell -c "
    from scripts.sync_testsim_from_dump import sync_from_dump
    sync_from_dump('/tmp/pre_pdf_testsim_dump.json')
    "

Side-effects:
- Replaces VerbrauchData / LandUse / RenewableData / WSData rows owned by testsim.
- Clears testsim's BalanceJob queue.
- Invalidates the four process-local caches.
"""
import json


def _maybe_float(v):
    if v is None or v == 'None':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def _maybe_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ('true', '1', 'yes')
    return bool(v)


def sync_from_dump(dump_path: str) -> None:
    from django.contrib.auth import get_user_model
    from simulator.models import VerbrauchData, LandUse, RenewableData, BalanceJob
    from simulator.ws_models import WSData
    from simulator.owner_scope import owner_scope

    with open(dump_path) as fh:
        dump = json.load(fh)

    User = get_user_model()
    u = User.objects.get(username='testsim')

    with owner_scope(u):
        # --- Verbrauch ---
        for code, fields in dump['verbrauch'].items():
            VerbrauchData.objects.filter(code=code).update(
                ziel=_maybe_float(fields['ziel']),
                user_percent=_maybe_float(fields['user_percent']),
                is_calculated=_maybe_bool(fields['is_calculated']),
                ziel_calculated=_maybe_bool(fields['ziel_calculated']),
            )

        # --- LandUse ---
        for code, fields in dump['landuse'].items():
            LandUse.objects.filter(code=code).update(
                status_ha=_maybe_float(fields['status_ha']),
                target_ha=_maybe_float(fields['target_ha']),
                user_percent=_maybe_float(fields['user_percent']),
            )

        # --- Renewable ---
        for code, fields in dump['renewable'].items():
            RenewableData.objects.filter(code=code).update(
                status_value=_maybe_float(fields['status_value']),
                target_value=_maybe_float(fields['target_value']),
                user_input=_maybe_float(fields['user_input']),
            )

        # --- WS (365 rows) ---
        for tag_str, fields in dump['ws'].items():
            tag = int(tag_str)
            WSData.objects.filter(tag_im_jahr=tag).update(
                verbrauch_promille=_maybe_float(fields['verbrauch_promille']),
                solar_promille=_maybe_float(fields['solar_promille']),
                wind_promille=_maybe_float(fields['wind_promille']),
                heizung_abwaerm_promille=_maybe_float(fields['heizung_abwaerm_promille']),
            )

        # --- Clear pending/old balance jobs for testsim ---
        deleted = BalanceJob.objects.filter(created_by=u).delete()

    # --- Invalidate caches (cross-process matters for the worker dyno) ---
    try:
        from simulator.recalc_cache import recalc_cache
        recalc_cache._cache.clear()
    except Exception:
        pass
    try:
        from simulator.formula_service import invalidate_auto_tokens_cache
        invalidate_auto_tokens_cache()
    except Exception:
        pass
    try:
        from simulator.ws365_orchestrator import _WS365_COMPUTE_CACHE
        _WS365_COMPUTE_CACHE.clear()
    except Exception:
        pass

    print(
        f"Sync OK. Verbrauch={len(dump['verbrauch'])} "
        f"LandUse={len(dump['landuse'])} Renewable={len(dump['renewable'])} "
        f"WS={len(dump['ws'])}  Cleared {deleted} BalanceJob refs."
    )
