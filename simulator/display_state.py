"""Helpers for keeping derived UI pages in sync after data mutations."""

from typing import Any

from django.core.cache import cache as django_cache

from simulator.models import CalculationRun


def invalidate_runtime_caches() -> None:
    """Clear caches that can otherwise make Bilanz/Cockpit show stale values."""
    try:
        django_cache.clear()
    except Exception:
        pass

    try:
        from simulator.recalc_cache import invalidate as invalidate_recalc_cache

        invalidate_recalc_cache()
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


def mark_display_state_changed(
    *,
    scope: str,
    triggered_by: str,
    duration_ms: int = 0,
    **summary: Any,
) -> CalculationRun:
    """Invalidate derived UI caches and create the marker used by Bilanz cache keys."""
    invalidate_runtime_caches()
    payload = {"scope": scope}
    payload.update(summary)
    return CalculationRun.objects.create(
        duration_ms=max(0, int(duration_ms or 0)),
        summary=payload,
        triggered_by=triggered_by,
    )
