import os

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Formula, FormulaVariable, LandUse, RenewableData, VerbrauchData, WS365Formula
from .ws_models import WSData


def _invalidate_formula_lookup_caches(*args, **kwargs):
    """Invalidate caches that TRUST signals (don't do their own signature checks).

    NOT invalidated here: recalc_cache. Its check_and_run does per-call
    signature hashing that correctly detects any DB state change. Clearing
    it from signals was harmful: the balance optimizer saves knobs 50+
    times per run; each save wiped the cache, forcing every settle round to
    re-do full recalcs cold instead of short-circuiting via signature match.
    Net effect was 5-10× slower balance on unbalanced workspaces.

    WS365 cache invalidation is kept because it uses pre-loaded ws_base_data
    + fixed_values as signature, which doesn't re-check on every call."""
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

    Phase B (T65): also reads installed_pmax_ely_gw + installed_pmax_rv_gw
    from the active Region (default DE: 194 / 261 GW). These replace the
    Track-1-leftover hardcoded annotations (194 GW, 261 GW) on the
    Jahresstrom diagram (T54 D4a, D4b).
    """
    del use_ws_overrides  # kept only for backward-compatible signature

    # Phase B (T65): fetch the active Region's installed-power constants.
    from simulator.region_scope import get_current_region_code

    region_code = get_current_region_code() or "DE"
    pmax_ely_gw = 194.0
    pmax_rv_gw = 261.0
    try:
        from simulator.models import Region

        region = Region.objects.get(code=region_code)
        pmax_ely_gw = float(region.installed_pmax_ely_gw or 0.0) or pmax_ely_gw
        pmax_rv_gw = float(region.installed_pmax_rv_gw or 0.0) or pmax_rv_gw
    except Exception:
        # If Region lookup fails (test DB without 0052 applied, etc.) keep
        # the DE defaults so the diagram still renders the right numbers.
        pass

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

    # Derived metrics for the Jahresstrom diagram labels (T54 D1-D4c).
    # Formulas confirmed by direct inspection of WS.xlsm cells on 2026-04-23:
    #   D1/D2: Tages = annual * TLproEingabeEinheit, where
    #          TLproEingabeEinheit = 365 / final_stromnetz
    #          (Wind + Hydro use "AE-adjusted" value = raw * (1 - ely_branch/m_total);
    #           PV + Bio use raw).
    #   D3:    four_source = pv + wind + hydro + bio; percent numerators
    #          are raw for PV/Bio and "AE-adjusted" for Wind/Hydro.
    #   D4c:   Abgleichdifferenz = gas_storage - t_value (gas tank drift).
    # See docs/stakeholder/HARDCODED_VALUES_TRACE.md §4 for the derivation.
    tl_factor = (365.0 / final_stromnetz) if final_stromnetz > 0 else 0.0
    ely_p2g_factor = (1.0 - (ely_branch_value / m_total)) if m_total > 0 else 0.0
    adjusted_wind = wind_value * ely_p2g_factor
    adjusted_hydro = hydro_value * ely_p2g_factor
    four_source_total = m_total + bio_value

    # D1 — source Tagesladungen
    pv_tages = pv_value * tl_factor
    wind_tages = adjusted_wind * tl_factor
    hydro_tages = adjusted_hydro * tl_factor
    bio_tages = bio_value * tl_factor

    # D2 — flow Tagesladungen (applied to every annual segment value)
    flow_n_value_tages = n_value * tl_factor
    flow_q_abregelung_tages = q_abregelung * tl_factor
    flow_n_to_right_tages = n_to_right * tl_factor
    flow_final_tages = final_stromnetz * tl_factor  # = 365 by definition
    flow_ely_branch_tages = ely_branch_value * tl_factor
    flow_n_output_branch_tages = n_output_branch * tl_factor
    # Gasspeicher-Direktverbrauch Tages matches Excel's L37 = L36 * TLproEingabeEinheit,
    # where L36 is the actual gas-tank throughput (solver-simulated einspeich_sum
    # post-efficiency = our gas_storage). The prior basis (ely_branch_value scenario
    # target × ETA_STROM_GAS) under-shot by the scenario-target-vs-solver-actual drift
    # (produced 83 instead of 87 on DE seed). Aligned 2026-04-24 per Pascal approval;
    # Excel L37 formula confirmed authoritative in SOURCE_GROUNDED_ANSWERS.md Q4.
    flow_gasspeicher_direkt_tages = gas_storage * tl_factor
    flow_gas_storage_tages = gas_storage * tl_factor
    flow_t_value_tages = t_value * tl_factor
    flow_reconversion_tages = t_output * tl_factor
    flow_storage_capacity_tages = storage_capacity * tl_factor

    # D3 — percent shares (NOTE asymmetric: PV/Bio use raw; Wind/Hydro use adjusted)
    pv_pct = (pv_value / four_source_total * 100.0) if four_source_total > 0 else 0.0
    wind_pct = (adjusted_wind / four_source_total * 100.0) if four_source_total > 0 else 0.0
    hydro_pct = (adjusted_hydro / four_source_total * 100.0) if four_source_total > 0 else 0.0
    bio_pct = (bio_value / four_source_total * 100.0) if four_source_total > 0 else 0.0

    # D4c — Abgleichdifferenz (gas-tank drift residual over the year)
    abgleichdifferenz = gas_storage - t_value
    abgleichdifferenz_tages = abgleichdifferenz * tl_factor

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
        # T54 D1 — source Tagesladungen
        "pv_tages": pv_tages,
        "wind_tages": wind_tages,
        "hydro_tages": hydro_tages,
        "bio_tages": bio_tages,
        # T54 D2 — flow Tagesladungen
        "flow_n_value_tages": flow_n_value_tages,
        "flow_q_abregelung_tages": flow_q_abregelung_tages,
        "flow_n_to_right_tages": flow_n_to_right_tages,
        "flow_final_tages": flow_final_tages,
        "flow_ely_branch_tages": flow_ely_branch_tages,
        "flow_n_output_branch_tages": flow_n_output_branch_tages,
        "flow_gasspeicher_direkt_tages": flow_gasspeicher_direkt_tages,
        "flow_gas_storage_tages": flow_gas_storage_tages,
        "flow_t_value_tages": flow_t_value_tages,
        "flow_reconversion_tages": flow_reconversion_tages,
        "flow_storage_capacity_tages": flow_storage_capacity_tages,
        # T54 D3 — percent shares (asymmetric formula matches Excel)
        "pv_pct": pv_pct,
        "wind_pct": wind_pct,
        "hydro_pct": hydro_pct,
        "bio_pct": bio_pct,
        # T54 D4c — Abgleichdifferenz
        "abgleichdifferenz": abgleichdifferenz,
        "abgleichdifferenz_tages": abgleichdifferenz_tages,
        # T54 D4a / D4b — installed-power region constants
        # (Phase B SR-004: sourced from Region.installed_pmax_*).
        "pmax_ely_gw": pmax_ely_gw,
        "pmax_rv_gw": pmax_rv_gw,
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
