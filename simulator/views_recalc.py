"""
Recalculation and state-management API view exports.

Zero-logic wrapper module to keep endpoint behavior unchanged while preparing
for deeper refactors.
"""

from .baseline_api import (
    create_baseline,
    create_scenario,
    delete_scenario,
    get_baseline_info,
    list_scenarios,
    rename_scenario,
    restore_baseline,
    restore_scenario,
)
from .input_api import (
    save_renewable_user_input,
    save_and_recalculate_verbrauch,
    save_verbrauch_user_input,
    update_verbrauch_bulk,
)
from .recalc_api import (
    recalc_verbrauch_view,
    recalc_ws_formulas_view,
    run_full_recalc_view,
    run_renewables_recalc_view,
    unified_recalc_view,
)
from .views import (
    save_all_user_inputs,
    update_user_percent,
)

__all__ = [
    "create_baseline",
    "create_scenario",
    "delete_scenario",
    "get_baseline_info",
    "list_scenarios",
    "recalc_verbrauch_view",
    "recalc_ws_formulas_view",
    "rename_scenario",
    "restore_baseline",
    "restore_scenario",
    "run_full_recalc_view",
    "run_renewables_recalc_view",
    "save_all_user_inputs",
    "save_and_recalculate_verbrauch",
    "save_renewable_user_input",
    "save_verbrauch_user_input",
    "unified_recalc_view",
    "update_user_percent",
    "update_verbrauch_bulk",
]
