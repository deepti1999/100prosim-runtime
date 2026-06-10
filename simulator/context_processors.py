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
    from simulator.admin_roles import (
        user_can_edit_formula_master_data,
        user_can_edit_landuse_master_data,
        user_can_edit_renewable_master_data,
        user_can_edit_workspace_values,
        user_can_manage_workspace_scenarios,
    )
    from simulator.models import Region
    from simulator.region_scope import get_current_region_code

    active_region_code = get_current_region_code() or "DE"
    active_region = None
    try:
        active_regions = list(Region.objects.filter(active=True).order_by("code"))
        active_region = next(
            (region for region in active_regions if region.code == active_region_code),
            None,
        )
        if active_region is None and active_regions:
            active_region = active_regions[0]
    except Exception:
        active_regions = []

    return {
        "active_regions": active_regions,
        "active_region_code": active_region_code,
        "active_region": active_region,
        "active_region_name": getattr(active_region, "display_name", "Deutschland"),
        "active_status_year": getattr(active_region, "status_year", 2023),
        "active_target_year": getattr(active_region, "target_year", 2045),
        "active_goal_description": getattr(
            active_region,
            "goal_description",
            "100 % Erneuerbare Energien",
        ),
        "active_data_source_label": getattr(
            active_region,
            "data_source_label",
            "Anlagenpark Deutschland 2023 [SMARD]",
        ),
        "can_edit_workspace_values": user_can_edit_workspace_values(request.user),
        "can_edit_landuse_master_data": user_can_edit_landuse_master_data(request.user),
        "can_edit_renewable_master_data": user_can_edit_renewable_master_data(request.user),
        "can_edit_formula_master_data": user_can_edit_formula_master_data(request.user),
        "can_manage_workspace_scenarios": user_can_manage_workspace_scenarios(request.user),
    }
