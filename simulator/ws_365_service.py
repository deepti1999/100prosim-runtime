"""WS 365 Days service compatibility wrapper.

This module re-exports the public WS365 API from dedicated submodules:
- ws365_core: core 365-day math, constants, and goal-seek helpers
- ws365_sector_balance: sector-balancing helpers
- ws365_orchestrator: high-level balancing workflows
"""

from .ws365_core import (
    ELECTROLYSIS_EFFICIENCY,
    FIXED_82_TARGET,
    GRID_LOSS_RATE,
    MOBILE_GAP_TOLERANCE,
    MOBILE_KNOB_MAX_JUMP,
    MOBILE_KNOB_STEP,
    PROCESS_GAP_TOLERANCE,
    RUECKVERSTROEMUNG_EFFICIENCY,
    TOTAL_ENERGY_GAP_TOLERANCE,
    _validate_required_landuse,
    calculate_365_days,
    calculate_required_landuse,
    calculate_required_landuse_wind,
    get_fixed_values,
    get_ws_base_data,
    goal_seek_optimal_solar,
    goal_seek_optimal_wind,
    update_renewable_from_ws365,
)
from .ws365_orchestrator import (
    apply_balanced_landuse,
    apply_balanced_landuse_sector_first,
    apply_balanced_wind_landuse,
    apply_balanced_wind_landuse_sector_first,
    get_ws_365_data,
)
from .ws365_sector_balance import _balance_heat_sectors_after_ws, _get_sector_totals

__all__ = [
    "GRID_LOSS_RATE",
    "ELECTROLYSIS_EFFICIENCY",
    "RUECKVERSTROEMUNG_EFFICIENCY",
    "FIXED_82_TARGET",
    "MOBILE_GAP_TOLERANCE",
    "TOTAL_ENERGY_GAP_TOLERANCE",
    "PROCESS_GAP_TOLERANCE",
    "MOBILE_KNOB_STEP",
    "MOBILE_KNOB_MAX_JUMP",
    "_validate_required_landuse",
    "get_ws_base_data",
    "get_fixed_values",
    "calculate_365_days",
    "goal_seek_optimal_solar",
    "goal_seek_optimal_wind",
    "get_ws_365_data",
    "update_renewable_from_ws365",
    "calculate_required_landuse",
    "calculate_required_landuse_wind",
    "_get_sector_totals",
    "_balance_heat_sectors_after_ws",
    "apply_balanced_landuse",
    "apply_balanced_landuse_sector_first",
    "apply_balanced_wind_landuse",
    "apply_balanced_wind_landuse_sector_first",
]
