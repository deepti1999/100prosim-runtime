"""
Phase B (T65) — template context processor for region awareness.

Exposes:
- active_regions: queryset of Region rows with active=True (for
  the nav dropdown).
- active_region_code: the user's currently-selected region code,
  defaulting to DE when no region is bound to the request thread.

Wired into settings.TEMPLATES so every template that extends
simulator/base.html sees these without per-view plumbing.
"""


def region_context(request):
    from simulator.models import Region
    from simulator.region_scope import get_current_region_code

    active_region_code = get_current_region_code() or "DE"
    try:
        active_regions = list(Region.objects.filter(active=True).order_by("code"))
    except Exception:
        active_regions = []

    return {
        "active_regions": active_regions,
        "active_region_code": active_region_code,
    }
