import os

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Formula, FormulaVariable, LandUse, RenewableData, VerbrauchData, WS365Formula
from .ws_models import WSData


def _invalidate_formula_lookup_caches(*args, **kwargs):
    """Step 1.6 + 1.7: invalidate formula_service + ws365 compute caches when
    any tracked row changes. Import lazily to avoid circular import."""
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

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

_cascade_in_progress = False

def _skip_signal_processing(kwargs):
    if kwargs.get("raw", False):
        return True
    return os.environ.get("DISABLE_SIMULATOR_SIGNALS", "false").lower() == "true"

def get_ws_constants():
    """
    Load WS efficiency constants from Formula entries (category='ws_constant').
    """
    eta_strom_gas = Formula.objects.get(key="WS_ETA_STROM_GAS", category="ws_constant")
    eta_gas_strom = Formula.objects.get(key="WS_ETA_GAS_STROM", category="ws_constant")
    abregelung_threshold = Formula.objects.get(key="WS_ABREGELUNG_THRESHOLD", category="ws_constant")
    return {
        "ETA_STROM_GAS": float(eta_strom_gas.expression),
        "ETA_GAS_STROM": float(eta_gas_strom.expression),
        "ABREGELUNG_THRESHOLD": float(abregelung_threshold.expression),
    }

def compute_ws_diagram_reference(use_ws_overrides: bool = True):
    """
    Annual electricity reference values based on Renewable formulas + WS 365 outputs.
    No WSData 366/367 usage.
    """
    del use_ws_overrides  # kept only for backward-compatible signature

    def renewable_value(code: str) -> float:
        row = RenewableData.objects.get(code=code)
        if row.is_fixed or not row.formula:
            if row.target_value is not None:
                return float(row.target_value)
            if row.status_value is not None:
                return float(row.status_value)
            return 0.0

        calc_status, calc_target = row.get_calculated_values(fail_fast=True)
        if calc_target is not None:
            return float(calc_target)
        if calc_status is not None:
            return float(calc_status)
        return 0.0

    ws_consts = get_ws_constants()

    pv_value = renewable_value("9.1.2")
    wind_value = renewable_value("9.1.1")
    hydro_value = renewable_value("9.1.3")
    bio_value = renewable_value("9.1.4")
    ely_branch_value = renewable_value("9.2.1.5.2")

    from .ws_365_service import get_ws_365_data

    ws_365_data = get_ws_365_data(run_goal_seek=False)
    current = ws_365_data["current"]
    daily_data = ws_365_data.get("daily_data") or []

    q_abregelung = float(current["abregelung_sum"])
    einspeich_sum = float(current["einspeich_sum"])
    n_output_branch = einspeich_sum / 0.65 if einspeich_sum > 0 else 0.0
    t_value = float(current["ausspeich_sum"])
    n_input_branch = q_abregelung

    m_total = pv_value + wind_value + hydro_value
    remaining_after_ely = m_total - ely_branch_value
    gas_storage = n_output_branch * ws_consts["ETA_STROM_GAS"]
    storage_capacity = max(
        (float(day.get("ladezust_abs_vorl_tl") or 0.0) for day in daily_data),
        default=0.0,
    )
    t_output = t_value * ws_consts["ETA_GAS_STROM"]

    n_value = m_total - ely_branch_value
    o_value = n_value - q_abregelung - n_output_branch
    n_to_right = o_value
    final_stromnetz = o_value + bio_value + (t_value * 0.585)

    factor = (remaining_after_ely / m_total) if m_total else 0.0
    solarstrom_366 = pv_value * factor
    windstrom_366 = wind_value * factor
    sonst_kraft_konstant_366 = hydro_value * factor

    h2_offer = ely_branch_value * ws_consts["ETA_STROM_GAS"]
    h2_surplus = n_output_branch * ws_consts["ETA_STROM_GAS"]

    return {
        "pv_value": pv_value,
        "wind_value": wind_value,
        "hydro_value": hydro_value,
        "bio_value": bio_value,
        "m_total": m_total,
        "ely_branch_value": ely_branch_value,
        "ely_offer": ely_branch_value,
        "h2_offer": h2_offer,
        "n_value": n_value,
        "q_abregelung": q_abregelung,
        "n_input_branch": n_input_branch,
        "n_output_branch": n_output_branch,
        "ely_surplus": n_output_branch,
        "gas_storage": gas_storage,
        "storage_capacity": storage_capacity,
        "t_value": t_value,
        "t_output": t_output,
        "n_to_right": n_to_right,
        "final_stromnetz": final_stromnetz,
        "stromverbr_raumwaerm_korr_366": final_stromnetz,
        "remaining_after_ely": remaining_after_ely,
        "solarstrom_366": solarstrom_366,
        "windstrom_366": windstrom_366,
        "sonst_kraft_konstant_366": sonst_kraft_konstant_366,
        "h2_surplus": h2_surplus,
    }

def recalculate_ws_data(stromverbr_override=None, use_diagram_reference=True):
    """
    Backward-compatible entrypoint.
    WS is now fully derived by ws_365_service; no row-level WSData recalculation.
    """
    del stromverbr_override
    del use_diagram_reference
    from .ws_365_service import get_ws_365_data

    return get_ws_365_data(run_goal_seek=False)

# Step 1.6: keep the formula lookup caches coherent with DB state.
# Covers the signal-fired mutation paths; bulk_update sites invalidate
# explicitly at the call site (see recalc_service.py / verbrauch_recalculator.py).
post_save.connect(_invalidate_formula_lookup_caches, sender=LandUse)
post_save.connect(_invalidate_formula_lookup_caches, sender=VerbrauchData)
post_save.connect(_invalidate_formula_lookup_caches, sender=RenewableData)
post_save.connect(_invalidate_formula_lookup_caches, sender=Formula)
post_save.connect(_invalidate_formula_lookup_caches, sender=FormulaVariable)


@receiver(post_save, sender=LandUse)
def update_renewable_calculations(sender, instance, created, **kwargs):
    del sender, created
    global _cascade_in_progress

    if _skip_signal_processing(kwargs):
        return
    if getattr(instance, "_skip_cascade", False):
        instance._skip_cascade = False
        return
    if _cascade_in_progress:
        return

    try:
        _cascade_in_progress = True
        from simulator.recalc_service import unified_recalc_all

        unified_recalc_all()
    except Exception as e:
        print(f"LandUse cascade error: {e}")
    finally:
        _cascade_in_progress = False

@receiver(post_delete, sender=LandUse)
def handle_landuse_deletion(sender, instance, **kwargs):
    del sender, instance
    if _skip_signal_processing(kwargs):
        return
    print("LandUse row deleted")

@receiver(post_save, sender=RenewableData)
def renewable_data_changed(sender, instance, **kwargs):
    del sender
    global _cascade_in_progress

    if _skip_signal_processing(kwargs):
        return
    if getattr(instance, "_skip_cascade", False):
        instance._skip_cascade = False
        return
    if _cascade_in_progress:
        return

    ws_input_codes = {"9.1.1", "9.1.2", "9.1.3", "9.1.4", "9.2.1.5.2"}
    if instance.code not in ws_input_codes:
        return

    try:
        _cascade_in_progress = True
        from simulator.recalc_service import unified_recalc_all

        unified_recalc_all()
    except Exception as e:
        print(f"Renewable cascade error: {e}")
    finally:
        _cascade_in_progress = False

@receiver(post_save, sender=VerbrauchData)
def verbrauch_data_changed(sender, instance, **kwargs):
    del sender
    if _skip_signal_processing(kwargs):
        return
    if getattr(instance, "_skip_verbrauch_recalc", False):
        return

    from django.db import transaction

    def trigger_renewable_recalc():
        try:
            from simulator.renewable_recalc import recalc_renewables_for_verbrauch

            recalc_renewables_for_verbrauch(instance.code)
        except Exception as e:
            print(f"Verbrauch cascade error for {instance.code}: {e}")

    transaction.on_commit(trigger_renewable_recalc)

@receiver(post_save, sender=WSData)
def ws_data_changed(sender, instance, **kwargs):
    del sender
    if _skip_signal_processing(kwargs):
        return
    if getattr(instance, "_skip_ws_cascade", False):
        instance._skip_ws_cascade = False
        return

    try:
        from .ws_365_service import get_ws_365_data

        if 1 <= int(instance.tag_im_jahr or 0) <= 365:
            get_ws_365_data(run_goal_seek=False)
    except Exception as e:
        print(f"WS input cascade error: {e}")

@receiver(post_save, sender=Formula)
@receiver(post_delete, sender=Formula)
def formula_changed(sender, instance, **kwargs):
    del sender
    if _skip_signal_processing(kwargs):
        return

    from django.core.cache import cache
    from django.db import transaction
    from simulator.formula_service import FormulaService

    cache.delete(f"formula_{instance.key}")
    try:
        FormulaService().clear_cache(instance.key)
    except Exception as e:
        print(f"Formula cache clear warning: {e}")

    def trigger_update():
        try:
            if instance.category == "ws":
                from .ws_365_service import get_ws_365_data

                get_ws_365_data(run_goal_seek=False)
            elif instance.category == "renewable":
                from simulator.recalc_service import unified_recalc_all

                unified_recalc_all()
            elif instance.category == "verbrauch":
                from simulator.verbrauch_recalculator import recalc_all_verbrauch

                recalc_all_verbrauch(trigger_code=f"formula:{instance.key}")
        except Exception as e:
            print(f"Error in formula-triggered update for {instance.key}: {e}")

    transaction.on_commit(trigger_update)

@receiver(post_save, sender=FormulaVariable)
@receiver(post_delete, sender=FormulaVariable)
def formula_variable_changed(sender, instance, **kwargs):
    del sender
    if _skip_signal_processing(kwargs):
        return
    if not instance.formula_id:
        return

    from django.core.cache import cache
    from simulator.formula_service import FormulaService

    try:
        formula_key = instance.formula.key
        cache.delete(f"formula_{formula_key}")
        FormulaService().clear_cache(formula_key)
    except Exception as e:
        print(f"Formula variable cache clear warning: {e}")

@receiver(post_save, sender=WS365Formula)
@receiver(post_delete, sender=WS365Formula)
def ws365_formula_changed(sender, instance, **kwargs):
    del sender
    if _skip_signal_processing(kwargs):
        return

    from django.db import transaction

    def trigger_update():
        try:
            from .ws_365_service import get_ws_365_data

            get_ws_365_data(run_goal_seek=False)
        except Exception as e:
            print(f"WS365 formula update warning for {instance.column_name}: {e}")

    transaction.on_commit(trigger_update)
