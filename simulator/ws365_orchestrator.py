"""WS 365 orchestration flows (solar/wind, sector-first variants)."""

import os

from .ws365_core import (
    MOBILE_GAP_TOLERANCE,
    PROCESS_GAP_TOLERANCE,
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
from .ws365_sector_balance import _balance_heat_sectors_after_ws, _get_sector_totals

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

# Step 1.7: process-local cache of the pure 365-day compute. Skips the
# ~48-85ms Python compute on cache hit. The side effect
# (update_renewable_from_ws365) still runs every call because the writes
# are value-compare idempotent (see ws365_core.py:436-438).
#
# Cache is keyed on (ws_base_data, fixed_values, run_goal_seek) hashed
# cheaply. Invalidated via signals (WSData/VerbrauchData/RenewableData
# post_save in signals.py) and via invalidate_ws365_cache() below.
_WS365_COMPUTE_CACHE = {}  # {(goal_seek,): (sig, response_dict)}


def _ws365_inputs_signature(ws_data, fixed_values):
    """Cheap signature from the already-loaded inputs — avoids hitting the DB
    again. Tuples of floats hash deterministically."""
    return (
        tuple(sorted(fixed_values.items())) if fixed_values else (),
        # ws_data contains arrays; hash each
        tuple(
            (k, hash(tuple(v)) if isinstance(v, list) else v)
            for k, v in sorted(ws_data.items())
        ) if ws_data else (),
    )


def invalidate_ws365_cache():
    """Clear the WS365 compute cache. Called from formula_service after
    bulk_updates, and via post_save signals in signals.py."""
    _WS365_COMPUTE_CACHE.clear()


def get_ws_365_data(run_goal_seek=False):
    """
    Main function to get all WS 365-day data.

    Args:
        run_goal_seek: If True, also run Goal Seek to find optimal solar

    Returns:
        Dictionary with all data for frontend display

    Caches the pure compute portion. Side-effect writes to RenewableData
    9.3.1 / 9.3.4 run on every call (they're idempotent value-compare saves).
    """
    ws_data = get_ws_base_data()
    fixed_values = get_fixed_values()
    sig = _ws365_inputs_signature(ws_data, fixed_values)
    cache_key = (bool(run_goal_seek),)

    cached = _WS365_COMPUTE_CACHE.get(cache_key)
    if cached is not None and cached[0] == sig:
        response = cached[1]
        # Side effect still fires — cheap when idempotent, safe when not.
        current_result = response.get('current') or {}
        # update_renewable_from_ws365 expects a ws_result dict; current matches shape
        update_renewable_from_ws365({
            'einspeich_sum': current_result.get('einspeich_sum', 0),
            'abregelung_sum': current_result.get('abregelung_sum', 0),
        })
        return response

    current_result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)

    update_renewable_from_ws365(current_result)
    
    response = {
        'current': {
            'solar': fixed_values['ziel_912'],
            'wind': fixed_values['ziel_911'],
            'sonst': fixed_values['ziel_913'],
            'bio': fixed_values['ziel_914'],
            'annual_demand': current_result['annual_demand'],
            'annual_electricity': current_result['annual_electricity'],
            'storage_drift': current_result['storage_drift'],
            'ladezust_day1': current_result['ladezust_day1'],
            'ladezust_day365': current_result['ladezust_day365'],
            'einspeich_sum': current_result['einspeich_sum'],
            'ausspeich_sum': current_result['ausspeich_sum'],
            'abregelung_sum': current_result['abregelung_sum'],
            'ueberschuss_sum': current_result['ueberschuss_sum'],
            'solar_strom_sum': current_result['solar_strom_sum'],
            'wind_strom_sum': current_result['wind_strom_sum'],
            'renewable_pct': current_result['renewable_pct'],
        },
        'daily_data': current_result['daily_data'],
    }
    
    if run_goal_seek:
        goal_seek_result = goal_seek_optimal_solar(ws_data, fixed_values)
        response['goal_seek'] = {
            'original_solar': goal_seek_result['original_solar'],
            'optimal_solar': goal_seek_result['optimal_solar'],
            'solar_change': goal_seek_result['solar_change'],
            'solar_change_pct': goal_seek_result['solar_change_pct'],
            'iterations': goal_seek_result['iterations'],
            'storage_drift': goal_seek_result['result']['storage_drift'],
            'annual_electricity': goal_seek_result['result']['annual_electricity'],
            'ladezust_day1': goal_seek_result['result']['ladezust_day1'],
            'ladezust_day365': goal_seek_result['result']['ladezust_day365'],
        }
        response['optimal_daily_data'] = goal_seek_result['result']['daily_data']

    _WS365_COMPUTE_CACHE[cache_key] = (sig, response)
    return response

def apply_balanced_landuse(
    include_sector_balance: bool = True,
    run_final_renewable_sync: bool = True
):
    """
    Run Goal Seek, calculate required LandUse, and update LU_2.1 in database.
    
    This function uses ONLY ws_365_service calculations (no WSData database):
    1. Runs Goal Seek to find optimal Solar (balanced storage for 365 days)
    2. Calculates required LU_2.1 to achieve that Solar
    3. Updates LU_2.1 in database
    4. Recalculates ONLY the renewable chain (LU_2.1 -> 1.2.1.2 -> 9.1.2)
    5. Updates 9.3.1 and 9.3.4 from WS 365 calculation
    6. Optional: balances heat + mobile sectors (10.4↔2.10, 10.5↔3.7, 10.6.1↔6.1)
       using active live formulas and bounded control knobs.
    
    NO WSData recalculation - all balance logic comes from ws_365_service.
    
    Returns:
        dict with all results
    """
    from .models import LandUse, RenewableData
    from django.db import transaction
    
    max_convergence_cycles = 3
    ws_drift_tolerance = 0.1
    heat_gap_tolerance = 100.0
    mobile_gap_tolerance = MOBILE_GAP_TOLERANCE
    enforce_total_energy_gap = False

    old_landuse = None
    required_landuse = None
    goal_seek_result = None
    heat_balance = None
    final_result = None
    new_912 = None
    completed_cycles = 0
    landuse_code = 'LU_2.1'
    landuse_name = 'LU_2.1'
    old_landuse_percent = None
    new_landuse_percent = None

    with transaction.atomic():
        for cycle_index in range(max_convergence_cycles):
            cycle_no = cycle_index + 1
            completed_cycles = cycle_no
            print(f" Convergence cycle {cycle_no}/{max_convergence_cycles}")

            # Step 1: Goal Seek on current WS inputs
            print(" Running Goal Seek...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            goal_seek_result = goal_seek_optimal_solar(
                ws_data,
                fixed_values,
                tolerance=ws_drift_tolerance
            )

            optimal_solar = goal_seek_result['optimal_solar']
            print(f"   Found optimal Solar: {optimal_solar:,.0f} GWh")
            print(f"   Storage drift at optimal: {goal_seek_result['result']['storage_drift']:.2f} GWh")

            # Step 2: Calculate required LU_2.1 from optimal solar
            landuse_result = calculate_required_landuse(optimal_solar)
            required_landuse = landuse_result['required_landuse']
            if old_landuse is None:
                old_landuse = landuse_result['current_landuse']
            print(
                f"    Required LU_2.1: {required_landuse:,.0f} ha "
                f"(change: {required_landuse - (landuse_result['current_landuse'] or 0):+,.0f} ha)"
            )

            # Step 3: Update LU_2.1 in DB
            lu_21 = LandUse.objects.select_related('parent').get(code='LU_2.1')
            landuse_name = lu_21.name or landuse_name
            if old_landuse_percent is None:
                if lu_21.user_percent is not None:
                    old_landuse_percent = float(lu_21.user_percent)
                elif lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0 and old_landuse is not None:
                    old_landuse_percent = (float(old_landuse) / float(lu_21.parent.target_ha)) * 100.0
            required_landuse = _validate_required_landuse(
                required_landuse,
                lu_21.parent.target_ha if lu_21.parent else None,
                'LU_2.1'
            )
            lu_21.target_ha = required_landuse
            if lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0:
                lu_21.user_percent = (required_landuse / lu_21.parent.target_ha) * 100.0
            lu_21._skip_cascade = True
            lu_21.save(update_fields=['target_ha', 'user_percent'])
            if lu_21.user_percent is not None:
                new_landuse_percent = float(lu_21.user_percent)
            elif lu_21.parent and lu_21.parent.target_ha and lu_21.parent.target_ha > 0:
                new_landuse_percent = (float(required_landuse) / float(lu_21.parent.target_ha)) * 100.0
            print(f"Updated LU_2.1 target_ha to {required_landuse:.2f} ha")

            print(" Recalculating renewable chain...")
            r_1211 = RenewableData.objects.get(code='1.2.1.1')
            r_1212 = RenewableData.objects.get(code='1.2.1.2')
            new_1212 = required_landuse * (r_1211.target_value or 0) / 1000
            r_1212.target_value = new_1212
            r_1212.save(skip_cascade=True)
            print(f"   1.2.1.2 = {new_1212:,.0f} GWh")

            r_11212 = RenewableData.objects.get(code='1.1.2.1.2')
            r_912 = RenewableData.objects.get(code='9.1.2')
            new_912 = (r_11212.target_value or 0) + new_1212
            r_912.target_value = new_912
            r_912.save(skip_cascade=True)
            print(f"   9.1.2 = {new_912:,.0f} GWh")

            # Step 5: WS calculation and sync 9.3.1 / 9.3.4 / 9.4.1
            print("Calculating WS 365 days with new Solar...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            final_result = calculate_365_days(fixed_values['ziel_912'], ws_data, fixed_values)
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941 = RenewableData.objects.get(code='9.4.1')
            r941.target_value = annual_electricity
            r941.is_fixed = True
            r941.formula = None
            r941.save(skip_cascade=True)
            print(f"   9.4.1 = {annual_electricity:,.0f} GWh (annual electricity from diagram, fixed)")

            final_drift = final_result['storage_drift']
            drift_ok = abs(final_drift) <= ws_drift_tolerance

            if include_sector_balance:
                # Step 6: Heat + mobile balancing
                print("Balancing sectors (10.4↔2.10, 10.5↔3.7, 10.6.1↔6.1)...")
                heat_balance = _balance_heat_sectors_after_ws()
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                mobile_after = heat_balance['after']['mobile_anwendungen']
                total_after = heat_balance['after'].get('total_energy')
                print(
                    f"   Gebäudewärme gap: {gw_after['gap']:.2f} GWh "
                    f"(demand {gw_after['demand']:,.0f} / supply {gw_after['supply']:,.0f})"
                )
                print(
                    f"   Prozesswärme gap: {pw_after['gap']:.2f} GWh "
                    f"(demand {pw_after['demand']:,.0f} / supply {pw_after['supply']:,.0f})"
                )
                print(
                    f"   Mobile Anwendungen gap: {mobile_after['gap']:.2f} GWh "
                    f"(demand {mobile_after['demand']:,.0f} / supply {mobile_after['supply']:,.0f})"
                )
                if total_after:
                    print(
                        f"   Total energy gap: {total_after['gap']:.2f} GWh "
                        f"(demand {total_after['demand']:,.0f} / supply {total_after['supply']:,.0f})"
                    )

                # Step 7: Re-check WS drift AFTER sector balancing
                ws_data_post_heat = get_ws_base_data()
                fixed_values_post_heat = get_fixed_values()
                final_result = calculate_365_days(
                    fixed_values_post_heat['ziel_912'],
                    ws_data_post_heat,
                    fixed_values_post_heat
                )
                update_renewable_from_ws365(final_result)

                annual_electricity = final_result.get('annual_electricity', 0)
                r941.target_value = annual_electricity
                r941.save(skip_cascade=True, update_fields=['target_value'])

                final_drift = final_result['storage_drift']
                drift_ok = abs(final_drift) <= ws_drift_tolerance
                heat_ok = (
                    abs(gw_after['gap']) <= heat_gap_tolerance and
                    abs(pw_after['gap']) <= PROCESS_GAP_TOLERANCE
                )
                mobile_ok = abs(mobile_after['gap']) <= mobile_gap_tolerance
                total_ok = True
                if enforce_total_energy_gap and total_after:
                    total_ok = abs(total_after['gap']) <= TOTAL_ENERGY_GAP_TOLERANCE
                print(
                    f"    Post-heat WS drift: {final_drift:.2f} GWh "
                    f"(target ±{ws_drift_tolerance})"
                )
                if drift_ok and heat_ok and mobile_ok and total_ok:
                    print("   Converged: WS + heat + mobile balanced")
                    break
            else:
                print(
                    f"    WS drift: {final_drift:.2f} GWh "
                    f"(target ±{ws_drift_tolerance})"
                )
                if drift_ok:
                    print("   Converged: WS electricity + drift balanced")
                    break
    
    if run_final_renewable_sync and final_result is not None:
        from simulator.recalc_service import recalc_all_renewables_full
        recalc_all_renewables_full(exclude_ws_dependent=False)

    # Final verification
    final_drift = final_result['storage_drift'] if final_result else 0
    annual_electricity = final_result.get('annual_electricity', 0) if final_result else 0
    print(f"\nBALANCE COMPLETE")
    print(f"   Storage Drift: {final_drift:.2f} GWh (target: 0)")
    print(f"   Annual Electricity (9.4.1): {annual_electricity:,.0f} GWh")
    
    return {
        'success': True,
        'old_landuse': old_landuse,
        'new_landuse': required_landuse,
        'landuse_change': required_landuse - old_landuse,
        'optimal_solar': optimal_solar,
        'new_solar': new_912,
        'storage_drift': final_drift,
        'annual_electricity': annual_electricity,
        'iterations': goal_seek_result['iterations'] if goal_seek_result else 0,
        'convergence_cycles': completed_cycles,
        'heat_balance': heat_balance,
        'landuse_code': landuse_code,
        'landuse_name': landuse_name,
        'old_landuse_percent': old_landuse_percent,
        'new_landuse_percent': new_landuse_percent,
    }

def apply_balanced_landuse_sector_first():
    """
    Sector-first balancing flow (Solar mode):
    1) Close sector gaps via sector knobs
    2) Re-run WS/electricity balancing (goal-seek + LU_2.1 update)

    This keeps the second button aligned with final Renewable page values.
    """
    from django.db import transaction
    from simulator.recalc_service import recalc_all_renewables_full

    with transaction.atomic():
        max_cycles = 2
        cycle_count = 0
        sector_balance = None
        ws_rebalance = None
        final_sector_totals = _get_sector_totals()
        final_drift = 0.0
        annual_electricity = 0.0
        sector_balance_ok = False
        drift_ok = False

        for idx in range(max_cycles):
            cycle_count = idx + 1
            print(f"Sector-first balancing cycle {cycle_count}/{max_cycles}...")
            sector_balance = _balance_heat_sectors_after_ws()

            print(" Rebalancing WS drift + electricity after sector tuning...")
            ws_rebalance = apply_balanced_landuse(
                include_sector_balance=False,
                run_final_renewable_sync=False
            )

            recalc_all_renewables_full(exclude_ws_dependent=False)
            final_sector_totals = _get_sector_totals()

            gw_gap = abs(float(final_sector_totals['gebaeudewaerme']['gap']))
            pw_gap = abs(float(final_sector_totals['prozesswaerme']['gap']))
            mobile_gap = abs(float(final_sector_totals['mobile_anwendungen']['gap']))
            sector_balance_ok = (
                gw_gap <= 100.0 and
                pw_gap <= PROCESS_GAP_TOLERANCE and
                mobile_gap <= MOBILE_GAP_TOLERANCE
            )

            final_drift = float(ws_rebalance.get('storage_drift') or 0.0)
            annual_electricity = float(ws_rebalance.get('annual_electricity') or 0.0)
            drift_ok = abs(final_drift) <= 0.1

            if sector_balance_ok and drift_ok:
                break

        ws_rebalance = ws_rebalance or {}
        sector_balance = sector_balance or {}
        final_drift = float(ws_rebalance.get('storage_drift') or 0.0)
        annual_electricity = float(ws_rebalance.get('annual_electricity') or 0.0)
        drift_ok = abs(final_drift) <= 0.1

        recalc_all_renewables_full(exclude_ws_dependent=False)
        final_sector_totals = _get_sector_totals()
        gw_gap = abs(float(final_sector_totals['gebaeudewaerme']['gap']))
        pw_gap = abs(float(final_sector_totals['prozesswaerme']['gap']))
        mobile_gap = abs(float(final_sector_totals['mobile_anwendungen']['gap']))
        sector_balance_ok = (
            gw_gap <= 100.0 and
            pw_gap <= PROCESS_GAP_TOLERANCE and
            mobile_gap <= MOBILE_GAP_TOLERANCE
        )

        warnings = []
        if not sector_balance_ok:
            warnings.append('Sector gaps are still outside tolerance after convergence cycles.')
        if not drift_ok:
            warnings.append('WS drift is still outside tolerance after final sync.')

        return {
            'success': True,
            'balance_mode': 'sector_then_ws',
            'convergence_cycles': cycle_count,
            'heat_balance': {
                'before': sector_balance.get('before'),
                'after_sector_knobs': sector_balance.get('after'),
                'after': final_sector_totals,
                'adjustments': sector_balance.get('adjustments'),
            },
            'ws_rebalance': {
                'old_landuse': ws_rebalance.get('old_landuse'),
                'new_landuse': ws_rebalance.get('new_landuse'),
                'landuse_change': ws_rebalance.get('landuse_change'),
                'optimal_solar': ws_rebalance.get('optimal_solar'),
                'new_solar': ws_rebalance.get('new_solar'),
                'iterations': ws_rebalance.get('iterations', 0),
                'convergence_cycles': ws_rebalance.get('convergence_cycles', 0),
                'landuse_code': ws_rebalance.get('landuse_code'),
                'landuse_name': ws_rebalance.get('landuse_name'),
                'old_landuse_percent': ws_rebalance.get('old_landuse_percent'),
                'new_landuse_percent': ws_rebalance.get('new_landuse_percent'),
            },
            'sector_balance_ok': sector_balance_ok,
            'drift_ok': drift_ok,
            'overall_balanced': sector_balance_ok and drift_ok,
            'storage_drift': final_drift,
            'annual_electricity': annual_electricity,
            'landuse_code': ws_rebalance.get('landuse_code'),
            'landuse_name': ws_rebalance.get('landuse_name'),
            'old_landuse': ws_rebalance.get('old_landuse'),
            'new_landuse': ws_rebalance.get('new_landuse'),
            'landuse_change': ws_rebalance.get('landuse_change'),
            'old_landuse_percent': ws_rebalance.get('old_landuse_percent'),
            'new_landuse_percent': ws_rebalance.get('new_landuse_percent'),
                'warning': ' '.join(warnings).strip(),
        }

def apply_balanced_wind_landuse(
    include_sector_balance: bool = True,
    run_final_renewable_sync: bool = True
):
    """
    Run Goal Seek with Wind as variable, calculate required LU_6, and update database.

    Flow mirrors apply_balanced_landuse(), but driver is Wind (9.1.1/LU_6)
    instead of Solar (9.1.2/LU_2.1). Heat/mobile balancing remains identical.
    """
    from .models import LandUse, RenewableData
    from django.db import transaction

    max_convergence_cycles = 3
    ws_drift_tolerance = 0.005
    heat_gap_tolerance = 100.0
    mobile_gap_tolerance = MOBILE_GAP_TOLERANCE
    enforce_total_energy_gap = False

    old_landuse = None
    required_landuse = None
    goal_seek_result = None
    heat_balance = None
    final_result = None
    new_911 = None
    completed_cycles = 0
    optimal_wind = None
    landuse_code = 'LU_6'
    landuse_name = 'LU_6'
    old_landuse_percent = None
    new_landuse_percent = None

    # Wind mode must not alter Solar/LU_2.1.
    r912_guard = RenewableData.objects.get(code='9.1.2')
    fixed_solar_912 = float(r912_guard.target_value or 0)
    lu21_guard = LandUse.objects.get(code='LU_2.1')
    fixed_lu21_target = float(lu21_guard.target_ha or 0)
    fixed_lu21_percent = lu21_guard.user_percent

    def _restore_frozen_solar_if_needed():
        r912_now = RenewableData.objects.get(code='9.1.2')
        if abs(float(r912_now.target_value or 0) - fixed_solar_912) > 1e-9:
            r912_now.target_value = fixed_solar_912
            r912_now.save(skip_cascade=True, update_fields=['target_value'])

    with transaction.atomic():
        for cycle_index in range(max_convergence_cycles):
            cycle_no = cycle_index + 1
            completed_cycles = cycle_no
            print(f" Wind convergence cycle {cycle_no}/{max_convergence_cycles}")

            # Step 1: Goal Seek on current WS inputs (Wind variable)
            print(" Running Wind Goal Seek...")
            _restore_frozen_solar_if_needed()
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            fixed_values['ziel_912'] = fixed_solar_912
            goal_seek_result = goal_seek_optimal_wind(
                ws_data,
                fixed_values,
                tolerance=ws_drift_tolerance
            )

            optimal_wind = goal_seek_result['optimal_wind']
            print(f"   Found optimal Wind: {optimal_wind:,.0f} GWh")
            print(f"   Storage drift at optimal: {goal_seek_result['result']['storage_drift']:.2f} GWh")

            # Step 2: Calculate required LU_6 from optimal wind
            landuse_result = calculate_required_landuse_wind(optimal_wind)
            required_landuse = landuse_result['required_landuse']
            if old_landuse is None:
                old_landuse = landuse_result['current_landuse']
            print(
                f"    Required LU_6: {required_landuse:,.0f} ha "
                f"(change: {required_landuse - (landuse_result['current_landuse'] or 0):+,.0f} ha)"
            )

            # Step 3: Update LU_6 in DB
            lu_6 = LandUse.objects.select_related('parent').get(code='LU_6')
            landuse_name = lu_6.name or landuse_name
            if old_landuse_percent is None:
                if lu_6.user_percent is not None:
                    old_landuse_percent = float(lu_6.user_percent)
                elif lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0 and old_landuse is not None:
                    old_landuse_percent = (float(old_landuse) / float(lu_6.parent.target_ha)) * 100.0
            required_landuse = _validate_required_landuse(
                required_landuse,
                lu_6.parent.target_ha if lu_6.parent else None,
                'LU_6'
            )
            lu_6.target_ha = required_landuse
            if lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0:
                lu_6.user_percent = (required_landuse / lu_6.parent.target_ha) * 100.0
            lu_6._skip_cascade = True
            lu_6.save(update_fields=['target_ha', 'user_percent'])
            if lu_6.user_percent is not None:
                new_landuse_percent = float(lu_6.user_percent)
            elif lu_6.parent and lu_6.parent.target_ha and lu_6.parent.target_ha > 0:
                new_landuse_percent = (float(required_landuse) / float(lu_6.parent.target_ha)) * 100.0
            print(f"Updated LU_6 target_ha to {required_landuse:.2f} ha")

            print(" Recalculating wind renewable chain...")
            r_211 = RenewableData.objects.get(code='2.1.1')
            r_211.target_value = required_landuse
            r_211.save(skip_cascade=True)
            print(f"   2.1.1 = {required_landuse:,.0f} ha")

            r_21111 = RenewableData.objects.get(code='2.1.1.1')
            r_21112 = RenewableData.objects.get(code='2.1.1.2')
            divisor_21111 = float(r_21111.target_value or 0)
            new_21112 = (required_landuse / divisor_21111) if divisor_21111 > 0 else 0
            r_21112.target_value = new_21112
            r_21112.save(skip_cascade=True)
            print(f"   2.1.1.2 = {new_21112:,.0f}")

            r_211121 = RenewableData.objects.get(code='2.1.1.2.1')
            r_211122 = RenewableData.objects.get(code='2.1.1.2.2')
            new_211122 = new_21112 * (r_211121.target_value or 0) / 1000
            r_211122.target_value = new_211122
            r_211122.save(skip_cascade=True)
            print(f"   2.1.1.2.2 = {new_211122:,.0f} GWh")

            r_22123 = RenewableData.objects.get(code='2.2.1.2.3')
            r_911 = RenewableData.objects.get(code='9.1.1')
            new_911 = (r_22123.target_value or 0) + new_211122
            r_911.target_value = new_911
            r_911.save(skip_cascade=True)
            print(f"   9.1.1 = {new_911:,.0f} GWh")

            # Step 5: WS calculation and sync 9.3.1 / 9.3.4 / 9.4.1
            print("Calculating WS 365 days with new Wind...")
            ws_data = get_ws_base_data()
            fixed_values = get_fixed_values()
            fixed_values['ziel_912'] = fixed_solar_912
            final_result = calculate_365_days(fixed_solar_912, ws_data, fixed_values)
            update_renewable_from_ws365(final_result)

            annual_electricity = final_result.get('annual_electricity', 0)
            r941 = RenewableData.objects.get(code='9.4.1')
            r941.target_value = annual_electricity
            r941.is_fixed = True
            r941.formula = None
            r941.save(skip_cascade=True)
            print(f"   9.4.1 = {annual_electricity:,.0f} GWh (annual electricity from diagram, fixed)")

            final_drift = final_result['storage_drift']
            drift_ok = abs(final_drift) <= ws_drift_tolerance

            if include_sector_balance:
                # Step 6: Heat + mobile balancing
                print("Balancing sectors (10.4↔2.10, 10.5↔3.7, 10.6.1↔6.1)...")
                heat_balance = _balance_heat_sectors_after_ws()
                gw_after = heat_balance['after']['gebaeudewaerme']
                pw_after = heat_balance['after']['prozesswaerme']
                mobile_after = heat_balance['after']['mobile_anwendungen']
                total_after = heat_balance['after'].get('total_energy')
                print(
                    f"   Gebäudewärme gap: {gw_after['gap']:.2f} GWh "
                    f"(demand {gw_after['demand']:,.0f} / supply {gw_after['supply']:,.0f})"
                )
                print(
                    f"   Prozesswärme gap: {pw_after['gap']:.2f} GWh "
                    f"(demand {pw_after['demand']:,.0f} / supply {pw_after['supply']:,.0f})"
                )
                print(
                    f"   Mobile Anwendungen gap: {mobile_after['gap']:.2f} GWh "
                    f"(demand {mobile_after['demand']:,.0f} / supply {mobile_after['supply']:,.0f})"
                )
                if total_after:
                    print(
                        f"   Total energy gap: {total_after['gap']:.2f} GWh "
                        f"(demand {total_after['demand']:,.0f} / supply {total_after['supply']:,.0f})"
                    )

                # Step 7: Re-check WS drift AFTER heat
                ws_data_post_heat = get_ws_base_data()
                fixed_values_post_heat = get_fixed_values()
                fixed_values_post_heat['ziel_912'] = fixed_solar_912
                _restore_frozen_solar_if_needed()
                final_result = calculate_365_days(
                    fixed_solar_912,
                    ws_data_post_heat,
                    fixed_values_post_heat
                )
                update_renewable_from_ws365(final_result)

                annual_electricity = final_result.get('annual_electricity', 0)
                r941.target_value = annual_electricity
                r941.save(skip_cascade=True, update_fields=['target_value'])

                final_drift = final_result['storage_drift']
                drift_ok = abs(final_drift) <= ws_drift_tolerance
                heat_ok = (
                    abs(gw_after['gap']) <= heat_gap_tolerance and
                    abs(pw_after['gap']) <= PROCESS_GAP_TOLERANCE
                )
                mobile_ok = abs(mobile_after['gap']) <= mobile_gap_tolerance
                total_ok = True
                if enforce_total_energy_gap and total_after:
                    total_ok = abs(total_after['gap']) <= TOTAL_ENERGY_GAP_TOLERANCE
                print(
                    f"    Post-heat WS drift: {final_drift:.2f} GWh "
                    f"(target ±{ws_drift_tolerance})"
                )
                if drift_ok and heat_ok and mobile_ok and total_ok:
                    print("   Converged: WS + heat + mobile balanced")
                    break
            else:
                print(
                    f"    WS drift: {final_drift:.2f} GWh "
                    f"(target ±{ws_drift_tolerance})"
                )
                if drift_ok:
                    print("   Converged: WS electricity + drift balanced (wind)")
                    break

        # Guard-restore: keep Solar/LU_2.1 untouched in wind mode.
        r912_now = RenewableData.objects.get(code='9.1.2')
        if abs(float(r912_now.target_value or 0) - fixed_solar_912) > 1e-9:
            r912_now.target_value = fixed_solar_912
            r912_now.save(skip_cascade=True, update_fields=['target_value'])

        lu21_now = LandUse.objects.get(code='LU_2.1')
        lu21_changed = (
            abs(float(lu21_now.target_ha or 0) - fixed_lu21_target) > 1e-9 or
            lu21_now.user_percent != fixed_lu21_percent
        )
        if lu21_changed:
            lu21_now.target_ha = fixed_lu21_target
            lu21_now.user_percent = fixed_lu21_percent
            lu21_now._skip_cascade = True
            lu21_now.save(update_fields=['target_ha', 'user_percent'])

        ws_data_final = get_ws_base_data()
        fixed_values_final = get_fixed_values()
        fixed_values_final['ziel_912'] = fixed_solar_912
        _restore_frozen_solar_if_needed()
        final_result = calculate_365_days(
            fixed_solar_912,
            ws_data_final,
            fixed_values_final
        )
        update_renewable_from_ws365(final_result)

        annual_electricity = final_result.get('annual_electricity', 0)
        r941 = RenewableData.objects.get(code='9.4.1')
        r941.target_value = annual_electricity
        r941.save(skip_cascade=True, update_fields=['target_value'])

    if run_final_renewable_sync and final_result is not None:
        from simulator.recalc_service import recalc_all_renewables_full
        recalc_all_renewables_full(exclude_ws_dependent=False)

    final_drift = final_result['storage_drift'] if final_result else 0
    annual_electricity = final_result.get('annual_electricity', 0) if final_result else 0
    print(f"\nWIND BALANCE COMPLETE")
    print(f"   Storage Drift: {final_drift:.2f} GWh (target: 0)")
    print(f"   Annual Electricity (9.4.1): {annual_electricity:,.0f} GWh")

    return {
        'success': True,
        'old_landuse': old_landuse,
        'new_landuse': required_landuse,
        'landuse_change': required_landuse - old_landuse,
        'optimal_wind': optimal_wind,
        'new_wind': new_911,
        'storage_drift': final_drift,
        'annual_electricity': annual_electricity,
        'iterations': goal_seek_result['iterations'] if goal_seek_result else 0,
        'convergence_cycles': completed_cycles,
        'heat_balance': heat_balance,
        'landuse_code': landuse_code,
        'landuse_name': landuse_name,
        'old_landuse_percent': old_landuse_percent,
        'new_landuse_percent': new_landuse_percent,
    }

def apply_balanced_wind_landuse_sector_first():
    """
    Sector-first balancing flow (Wind mode):
    1) Close sector gaps via sector knobs
    2) Re-run WS/electricity balancing with Wind goal-seek + LU_6 update
    """
    from django.db import transaction
    from simulator.recalc_service import recalc_all_renewables_full

    with transaction.atomic():
        max_cycles = 2
        cycle_count = 0
        sector_balance = None
        ws_rebalance = None
        final_sector_totals = _get_sector_totals()
        final_drift = 0.0
        annual_electricity = 0.0
        sector_balance_ok = False
        drift_ok = False

        for idx in range(max_cycles):
            cycle_count = idx + 1
            print(f"Wind sector-first balancing cycle {cycle_count}/{max_cycles}...")
            sector_balance = _balance_heat_sectors_after_ws()

            print(" Rebalancing WS drift + electricity after sector tuning (wind)...")
            ws_rebalance = apply_balanced_wind_landuse(
                include_sector_balance=False,
                run_final_renewable_sync=False
            )

            recalc_all_renewables_full(exclude_ws_dependent=False)
            final_sector_totals = _get_sector_totals()

            gw_gap = abs(float(final_sector_totals['gebaeudewaerme']['gap']))
            pw_gap = abs(float(final_sector_totals['prozesswaerme']['gap']))
            mobile_gap = abs(float(final_sector_totals['mobile_anwendungen']['gap']))
            sector_balance_ok = (
                gw_gap <= 100.0 and
                pw_gap <= PROCESS_GAP_TOLERANCE and
                mobile_gap <= MOBILE_GAP_TOLERANCE
            )

            final_drift = float(ws_rebalance.get('storage_drift') or 0.0)
            annual_electricity = float(ws_rebalance.get('annual_electricity') or 0.0)
            drift_ok = abs(final_drift) <= 0.1

            if sector_balance_ok and drift_ok:
                break

        ws_rebalance = ws_rebalance or {}
        sector_balance = sector_balance or {}
        final_drift = float(ws_rebalance.get('storage_drift') or 0.0)
        annual_electricity = float(ws_rebalance.get('annual_electricity') or 0.0)
        drift_ok = abs(final_drift) <= 0.1

        recalc_all_renewables_full(exclude_ws_dependent=False)
        final_sector_totals = _get_sector_totals()
        gw_gap = abs(float(final_sector_totals['gebaeudewaerme']['gap']))
        pw_gap = abs(float(final_sector_totals['prozesswaerme']['gap']))
        mobile_gap = abs(float(final_sector_totals['mobile_anwendungen']['gap']))
        sector_balance_ok = (
            gw_gap <= 100.0 and
            pw_gap <= PROCESS_GAP_TOLERANCE and
            mobile_gap <= MOBILE_GAP_TOLERANCE
        )

        warnings = []
        if not sector_balance_ok:
            warnings.append('Sector gaps are still outside tolerance after convergence cycles.')
        if not drift_ok:
            warnings.append('WS drift is still outside tolerance after final sync.')

        return {
            'success': True,
            'balance_mode': 'sector_then_ws_wind',
            'convergence_cycles': cycle_count,
            'heat_balance': {
                'before': sector_balance.get('before'),
                'after_sector_knobs': sector_balance.get('after'),
                'after': final_sector_totals,
                'adjustments': sector_balance.get('adjustments'),
            },
            'ws_rebalance': {
                'old_landuse': ws_rebalance.get('old_landuse'),
                'new_landuse': ws_rebalance.get('new_landuse'),
                'landuse_change': ws_rebalance.get('landuse_change'),
                'optimal_wind': ws_rebalance.get('optimal_wind'),
                'new_wind': ws_rebalance.get('new_wind'),
                'iterations': ws_rebalance.get('iterations', 0),
                'convergence_cycles': ws_rebalance.get('convergence_cycles', 0),
                'landuse_code': ws_rebalance.get('landuse_code'),
                'landuse_name': ws_rebalance.get('landuse_name'),
                'old_landuse_percent': ws_rebalance.get('old_landuse_percent'),
                'new_landuse_percent': ws_rebalance.get('new_landuse_percent'),
            },
            'sector_balance_ok': sector_balance_ok,
            'drift_ok': drift_ok,
            'overall_balanced': sector_balance_ok and drift_ok,
            'storage_drift': final_drift,
            'annual_electricity': annual_electricity,
            'landuse_code': ws_rebalance.get('landuse_code'),
            'landuse_name': ws_rebalance.get('landuse_name'),
            'old_landuse': ws_rebalance.get('old_landuse'),
            'new_landuse': ws_rebalance.get('new_landuse'),
            'landuse_change': ws_rebalance.get('landuse_change'),
            'old_landuse_percent': ws_rebalance.get('old_landuse_percent'),
            'new_landuse_percent': ws_rebalance.get('new_landuse_percent'),
            'warning': ' '.join(warnings).strip(),
        }
