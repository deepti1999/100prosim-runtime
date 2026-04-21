import time
import os
from typing import Dict, Any, List

from django.db import transaction
from django.utils import timezone

from simulator.models import LandUse, RenewableData, VerbrauchData
from simulator.verbrauch_recalculator import recalc_all_verbrauch

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

def full_chain_recalc(verbose: bool = False) -> Dict[str, Any]:
    """
     FULL CHAIN RECALCULATION - The CORRECT order for all dependencies!
    
    This function ensures the proper chain is followed:
    1. Recalculate INPUT renewables (9.1.x, 9.2.x, 10.x excluding 9.3.1, 9.3.4)
    2. Recalculate WS data (uses renewable inputs)
    3. Recalculate ALL renewables again (so 10.1 includes stored 9.3.1, 9.3.4 values)
    
    This breaks the circular dependency and ensures 10.1 is always correct.
    
    Returns:
        Dict with stats about what was updated
    """
    stats = {
        'input_renewables': 0,
        'ws_updated': 0,
        'output_renewables': 0,
        'final_renewables': 0,
    }
    
    if verbose:
        print("\n FULL CHAIN RECALC: Starting...")
    
    stats['input_renewables'] = recalc_all_renewables_full(exclude_ws_dependent=True)
    if verbose:
        print(f"   Step 1: Input renewables updated: {stats['input_renewables']}")
    
    from simulator.ws_365_service import get_ws_365_data
    ws_data = get_ws_365_data(run_goal_seek=False)
    stats['ws_updated'] = len(ws_data.get('daily_data', []))
    if verbose:
        print(f"   Step 2: WS days computed: {stats['ws_updated']}")
    
    stats['final_renewables'] = recalc_all_renewables_full(exclude_ws_dependent=False)
    if verbose:
        print(f"   Step 3: Final renewables updated: {stats['final_renewables']}")
    
    if verbose:
        print(" FULL CHAIN RECALC: Complete!\n")
    
    return stats

def full_chain_recalc_for_landuse(landuse_code: str, verbose: bool = False) -> Dict[str, Any]:
    """
     FULL CHAIN RECALCULATION for a specific LandUse change.
    
    When a LandUse value changes, this ensures the full cascade:
    1. LandUse dependents (direct renewable connections)
    2. WS recalculation
    3. Final renewable totals (10.1 etc.)
    
    Args:
        landuse_code: The code of the LandUse that changed (e.g., 'LU_2.1')
        verbose: If True, print debug info
    
    Returns:
        Dict with stats
    """
    stats = {
        'landuse_dependents': 0,
        'ws_updated': 0,
        'output_renewables': 0,
        'final_renewables': 0,
    }
    
    if verbose:
        print(f"\n FULL CHAIN for {landuse_code}: Starting...")
    
    try:
        lu = LandUse.objects.get(code=landuse_code)
    except LandUse.DoesNotExist:
        if verbose:
            print(f"   LandUse {landuse_code} not found!")
        return stats
    
    # STEP 1: Recalculate direct LandUse dependents
    lu._recalculate_renewable_dependents()
    if verbose:
        print(f"   Step 1: LandUse dependents recalculated")
    
    from simulator.ws_365_service import get_ws_365_data
    ws_data = get_ws_365_data(run_goal_seek=False)
    stats['ws_updated'] = len(ws_data.get('daily_data', []))
    if verbose:
        print(f"   Step 2: WS days computed: {stats['ws_updated']}")
    
    stats['final_renewables'] = recalc_all_renewables_full(exclude_ws_dependent=False)
    if verbose:
        print(f"   Step 3: Final renewables updated: {stats['final_renewables']}")
    
    if verbose:
        print(f" FULL CHAIN for {landuse_code}: Complete!\n")
    
    return stats

def recalc_all_renewables_full(exclude_ws_dependent: bool = False) -> int:
    """
    Recalculate all non-fixed RenewableData items in MULTIPLE PASSES to ensure
    children are calculated before parents (since parents sum their children).

    Pass 1: Most specific items (longest codes like 10.3.1.1)
    Pass 2: Mid-level items (like 10.3.1, 10.4.1)
    Pass 3: Parent items (like 10.3, 10.4)
    Pass 4: Top-level (like 10.1, 10.2)

    Uses fresh LandUse and Verbrauch lookups. Updates in-memory lookups after
    each calculation so downstream formulas see fresh values.

    Args:
        exclude_ws_dependent: Legacy flag (kept for compatibility). 9.3.1/9.3.4 are
        always excluded from calculation and treated as fixed.

    NOTE: 9.3.4 and 9.3.1 are fixed and never set from WS output.
    """
    from simulator.recalc_cache import check_and_run, renewables_inputs_signature
    return check_and_run(
        'recalc_all_renewables_full',
        renewables_inputs_signature,
        lambda: _recalc_all_renewables_full_impl(exclude_ws_dependent),
    )


def _recalc_all_renewables_full_impl(exclude_ws_dependent: bool = False) -> int:
    from simulator.models import Formula
    from calculation_engine.renewable_engine import RenewableCalculator

    # Fixed codes (never recalculated)
    WS_DEPENDENT_CODES = {'9.3.1', '9.3.4'}

    formula_codes = list(
        Formula.objects.filter(category="renewable", is_active=True).values_list("key", flat=True)
    )
    # Get only base codes (not _target or _ziel variants)
    base_codes = set(c for c in formula_codes if not c.endswith('_target') and not c.endswith('_ziel') and not c.endswith('_ziel_target'))
    
    # Always exclude fixed codes from recalculation
    base_codes = base_codes - WS_DEPENDENT_CODES
    
    dependent_items = list(RenewableData.objects.filter(code__in=base_codes))
    
    dependent_items.sort(key=lambda x: (-len(x.code.split('.')), x.code), reverse=False)
    dependent_items.sort(key=lambda x: (-len(x.code), x.code), reverse=False)

    landuse_data = {
        lu.code: {
            "status_ha": lu.status_ha or 0,
            "target_ha": lu.target_ha or 0,
        }
        for lu in LandUse.objects.all()
    }
    verbrauch_data = {
        v.code: {"status": v.status or 0, "ziel": v.ziel or 0}
        for v in VerbrauchData.objects.all()
    }
    renewable_data = {
        r.code: {
            "status_value": r.status_value or 0,
            "target_value": r.target_value or 0,
        }
        for r in RenewableData.objects.all()
    }

    calculator = RenewableCalculator()
    formula_map = {
        f.key: f
        for f in Formula.objects.filter(category="renewable", is_active=True).prefetch_related("variables")
    }
    calculator._formula_cache = dict(formula_map)
    calculator._renewable_cache = {r.code: r for r in RenewableData.objects.all()}
    target_formula_keys = {
        key
        for item in dependent_items
        for key in (f"{item.code}_target", f"{item.code}_ziel_target", f"{item.code}_ziel")
    }
    calculator._target_formula_cache = {key: formula_map.get(key) for key in target_formula_keys}
    updated_count = 0

    def materially_changed(old_value, new_value, rel_tol=1e-12) -> bool:
        """
        Ignore tiny float noise so we don't spin extra passes/writes.
        Keep tolerance extremely tight to preserve existing math behavior.
        """
        if new_value is None:
            return False
        if old_value is None:
            return True
        delta = abs(float(old_value) - float(new_value))
        scale = max(1.0, abs(float(old_value)), abs(float(new_value)))
        return delta > (rel_tol * scale)
    
    max_passes = 8
    for pass_num in range(1, max_passes + 1):
        calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)
        status_lookup = calculator.cache.get("status_lookup", {})
        target_lookup = calculator.cache.get("target_lookup", {})
        changed_items = []
        for item in dependent_items:
            calc_status, calc_target = calculator.calculate(item.code, fail_fast=False)

            values_changed = False
            if materially_changed(item.status_value, calc_status):
                item.status_value = calc_status
                values_changed = True

            if materially_changed(item.target_value, calc_target):
                item.target_value = calc_target
                values_changed = True

            if values_changed:
                renewable_data[item.code] = {
                    "status_value": item.status_value or 0,
                    "target_value": item.target_value or 0,
                }
                renewable_key = f"RenewableData_{item.code}"
                status_lookup[renewable_key] = float(item.status_value or 0)
                target_lookup[renewable_key] = float(item.target_value or 0)
                changed_items.append(item)

        changed_in_pass = len(changed_items)
        if changed_in_pass:
            now = timezone.now()
            for row in changed_items:
                row.updated_at = now
            RenewableData.objects.bulk_update(
                changed_items,
                ["status_value", "target_value", "updated_at"],
                batch_size=500,
            )
            updated_count += changed_in_pass

        # Converged: no further changes in this pass.
        if changed_in_pass == 0:
            break

    return updated_count

def unified_recalc_all() -> Dict[str, Any]:
    """
     UNIFIED RECALCULATION - Handles circular dependency correctly!
    
    This is the PROPER way to recalculate everything without infinite loops.
    
    Order (CRITICAL!):
    1. Recalculate INPUT renewables (9.1.x, 9.2.x, 10.x) - EXCLUDING 9.3.1, 9.3.4
    2. Update 9.3.1 and 9.3.4 from WS 365-day calculation (NOT old WSData!)
    3. Recalculate ALL renewables (so 10.1 includes stored 9.3.1, 9.3.4 values)
    
    NOTE: WSData (366 rows) is NO LONGER recalculated here.
    The WS 365 service uses its own calculation logic directly from Renewable inputs.
    
    This breaks the circular dependency because:
    - Step 1 provides inputs to WS 365
    - Step 2 calculates WS 365 and updates 9.3.1/9.3.4 in DB
    - Step 3 recalculates totals (10.1) to include stored 9.3.x values
    
    After this, ALL values are consistent and no further recalculation needed.
    """
    start = time.perf_counter()
    stats = {
        'input_renewables': 0,
        'ws365_updated': False,
        'final_renewables': 0,
        'duration_ms': 0,
    }
    
    print("\n" + "="*60)
    print(" UNIFIED RECALCULATION - Renewables + WS 365")
    print("="*60)
    
    with transaction.atomic():
        print(f"\n---  UNIFIED RECALCULATION ---")
        
        print(f"\nStep 1/3: Recalculating INPUT renewables (excluding 9.3.1, 9.3.4)...")
        input_updates = recalc_all_renewables_full(exclude_ws_dependent=True)
        stats['input_renewables'] = input_updates
        print(f"   Updated {input_updates} input renewables")
        
        print("\n Step 2/3: Updating 9.3.1 and 9.3.4 from WS 365 calculation...")
        from simulator.ws_365_service import get_ws_365_data
        get_ws_365_data(run_goal_seek=False)
        stats['ws365_updated'] = True
        print(f"   Updated 9.3.1 and 9.3.4 from WS 365")
        
        print("\nStep 3/3: Recalculating ALL renewables (updating totals)...")
        final_updates = recalc_all_renewables_full(exclude_ws_dependent=False)
        stats['final_renewables'] = final_updates
        print(f"   Updated {final_updates} renewables (including totals)")
    
    stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
    
    print("\n" + "="*60)
    print(f"UNIFIED RECALCULATION COMPLETE in {stats['duration_ms']}ms")
    print(f"   Input Renewables: {stats['input_renewables']}")
    print(f"   WS 365 Updated: {stats['ws365_updated']}")
    print("   9.3.1/9.3.4: target from WS 365, status = 0")
    print(f"   Final Renewables (with totals): {stats['final_renewables']}")
    print("="*60 + "\n")
    
    return stats

def _balance_energy_with_ws365(
    driver_code: str = "LU_2.1",
    energy_tolerance: float = 1.0,
    max_iter: int = 5,
) -> Dict[str, Any]:
    """
    Balance total energy gap by adjusting one LandUse driver using WS 365 flows only.
    This path avoids legacy WSData 366/367 balancing helpers.
    """
    from calculation_engine.bilanz_engine import calculate_bilanz_data, get_renewable_value
    from simulator.goal_seek import goal_seek
    from simulator.ws_365_service import get_ws_365_data

    try:
        lu = LandUse.objects.get(code=driver_code)
    except LandUse.DoesNotExist:
        return {"is_balanced": False, "error": f"LandUse {driver_code} not found"}

    initial_bilanz = calculate_bilanz_data()
    cached_demand = initial_bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0

    def set_and_gap(target_ha: float):
        lu.target_ha = max(0, target_ha)
        lu.save(skip_cascade=True, force_recalc=False)

        lu._recalculate_renewable_dependents()
        recalc_all_renewables_full(exclude_ws_dependent=True)
        get_ws_365_data(run_goal_seek=False)
        recalc_all_renewables_full(exclude_ws_dependent=False)

        renewable_total = get_renewable_value("10.1", use_target=True, fail_fast=False) or 0
        gap = cached_demand - renewable_total
        return gap, cached_demand, renewable_total, lu.target_ha

    base_ha = lu.target_ha or 0
    gap0, demand0, renewable0, ha0 = set_and_gap(base_ha)

    if abs(gap0) <= energy_tolerance:
        return {
            "is_balanced": True,
            "initial_gap": gap0,
            "final_gap": gap0,
            "initial_ha": ha0,
            "final_ha": ha0,
            "demand": demand0,
            "renewable": renewable0,
            "driver": driver_code,
            "iterations": 0,
        }

    x1 = ha0 * 1.1 + 100 if gap0 > 0 and ha0 == 0 else (ha0 * 1.1 if gap0 > 0 else max(ha0 * 0.9, 0))

    def gap_func(area):
        g, _, _, _ = set_and_gap(area)
        return g

    final_ha = goal_seek(gap_func, ha0, x1, target=0.0, tol=energy_tolerance, max_iter=max_iter)
    final_gap, final_demand, final_renewable, final_ha = set_and_gap(final_ha)

    return {
        "is_balanced": abs(final_gap) <= energy_tolerance,
        "initial_gap": gap0,
        "final_gap": final_gap,
        "initial_ha": ha0,
        "final_ha": final_ha,
        "demand": final_demand,
        "renewable": final_renewable,
        "driver": driver_code,
    }

def unified_recalc_and_balance(balance_after=True, ws_tolerance=10.0, energy_tolerance=1.0, max_balance_cycles=6) -> Dict[str, Any]:
    """
     UNIFIED RECALCULATION WITH AUTO-BALANCE
    
    This is the COMPLETE recalculation function that:
    1. Runs unified recalculation (handles circular dependency)
    2. Automatically balances the system (if balance_after=True)
    
    The flow is:
    1. Recalculate INPUT renewables (9.1.x, 9.2.x, 10.x) - EXCLUDING 9.3.1, 9.3.4
    2. Recalculate WS data (uses input renewable values)  
    3. Keep 9.3.1/9.3.4 fixed from DB (no WS -> renewable writes)
    4. (Optional) Balance the system by adjusting LandUse until supply=demand
    
    Args:
        balance_after: If True, run balance after recalculation
        ws_tolerance: Tolerance for WS balance (GWh)
        energy_tolerance: Tolerance for energy balance (GWh)
        max_balance_cycles: Max iterations for balance loop
        
    Returns:
        Dict with stats for recalc and balance
    """
    start = time.perf_counter()
    
    stats = {
        'recalc': {},
        'balance': {},
        'is_balanced': False,
        'duration_ms': 0,
    }
    
    print("\n" + "="*70)
    print(" UNIFIED RECALCULATION + AUTO-BALANCE")
    print("="*70)
    
    # Step 1: Run unified recalculation
    print("\nPHASE 1: Unified Recalculation...")
    recalc_stats = unified_recalc_all()
    stats['recalc'] = recalc_stats
    
    if not balance_after:
        stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
        print(f"\nRecalculation complete (no balance). Duration: {stats['duration_ms']}ms")
        return stats
    
    # Step 2: Run balance (only if requested)
    print("\n PHASE 2: Auto-Balance...")
    
    from calculation_engine.bilanz_engine import calculate_bilanz_data, get_renewable_value
    
    # Check current balance gap
    bilanz = calculate_bilanz_data()
    demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
    
    renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0
    initial_gap = demand - renewable
    
    print(f"   Current Demand: {demand:,.0f} GWh")
    print(f"   Current Renewable (10.1 total): {renewable:,.0f} GWh")
    print(f"   Gap: {initial_gap:,.2f} GWh")
    
    if abs(initial_gap) <= energy_tolerance:
        stats['balance'] = {
            'is_balanced': True,
            'initial_gap': initial_gap,
            'final_gap': initial_gap,
            'iterations': 0,
            'message': 'Already balanced'
        }
        stats['is_balanced'] = True
        stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
        print(f"\nSystem already balanced! Gap: {initial_gap:.2f} GWh")
        return stats
    
    def _ws_365_balance_snapshot() -> Dict[str, Any]:
        """
        Source WS balance from WS 365 outputs only (no WSData row 366/367 reads).
        """
        from simulator.ws_365_service import get_ws_365_data
        ws_data = get_ws_365_data(run_goal_seek=False)
        current = ws_data.get("current", {})
        storage_drift = float(current.get("storage_drift", 0) or 0)
        return {
            "is_balanced": abs(storage_drift) <= ws_tolerance,
            "final_balance": storage_drift,
        }

    # Run balance cycles - FAST version with fewer iterations
    balance_cycles = []
    for cycle in range(max_balance_cycles):
        print(f"\n   --- Balance Cycle {cycle + 1}/{max_balance_cycles} ---")
        
        # Balance energy (adjust LandUse) using WS 365 flows only.
        energy_result = _balance_energy_with_ws365(
            driver_code="LU_2.1",
            energy_tolerance=energy_tolerance,
            max_iter=5,
        )
        if energy_result.get("error"):
            stats['balance'] = {'error': energy_result["error"], 'is_balanced': False}
            stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
            return stats
        energy_balanced = energy_result.get("is_balanced", False)
        energy_gap = energy_result.get("final_gap", 0)
        print(f"   Energy: balanced={energy_balanced}, gap={energy_gap:.2f}")
        
        # EARLY EXIT: If energy is balanced, check if we're done
        if energy_balanced and abs(energy_gap) <= energy_tolerance:
            # Quick WS check from WS 365 service output only
            ws_state = _ws_365_balance_snapshot()
            ws_balance_value = ws_state["final_balance"]
            
            if abs(ws_balance_value) <= ws_tolerance:
                print(f"   EARLY EXIT - Both balanced!")
                stats['balance'] = {
                    'is_balanced': True,
                    'initial_gap': initial_gap,
                    'final_gap': energy_gap,
                    'ws_balance': ws_balance_value,
                    'iterations': cycle + 1,
                    'message': f'Balanced after {cycle + 1} cycles (early exit)'
                }
                stats['is_balanced'] = True
                stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
                return stats
        
        # Check WS storage from WS 365 service output only
        ws_state = _ws_365_balance_snapshot()
        ws_balanced = ws_state["is_balanced"]
        ws_balance_value = ws_state["final_balance"]
        print(f"   WS: balanced={ws_balanced}, ladezustand_netto={ws_balance_value:.2f}")
        
        # Quick recalc of just totals (faster)
        recalc_all_renewables_full()
        
        bilanz = calculate_bilanz_data()
        demand = bilanz.get("verbrauch_gesamt", {}).get("ziel", {}).get("gesamt", 0) or 0
        renewable = get_renewable_value('10.1', use_target=True, fail_fast=False) or 0
        final_gap = demand - renewable
        
        balance_cycles.append({
            "cycle": cycle + 1,
            "energy_gap": energy_gap,
            "ws_balance": ws_balance_value,
            "final_gap": final_gap,
        })
        
        # Check if balanced - EXIT IMMEDIATELY
        if abs(final_gap) <= energy_tolerance and abs(ws_balance_value) <= ws_tolerance:
            stats['balance'] = {
                'is_balanced': True,
                'initial_gap': initial_gap,
                'final_gap': final_gap,
                'ws_balance': ws_balance_value,
                'iterations': cycle + 1,
                'cycles': balance_cycles,
                'message': f'Balanced after {cycle + 1} cycles'
            }
            stats['is_balanced'] = True
            stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
            print(f"\nFULLY BALANCED after {cycle + 1} cycles!")
            print(f"   Final Gap: {final_gap:.2f} GWh")
            print(f"   WS Balance: {ws_balance_value:.2f} GWh")
            return stats
    
    # Max cycles reached
    stats['balance'] = {
        'is_balanced': False,
        'initial_gap': initial_gap,
        'final_gap': final_gap,
        'ws_balance': ws_balance_value,
        'iterations': max_balance_cycles,
        'cycles': balance_cycles,
        'message': f'Max cycles ({max_balance_cycles}) reached'
    }
    stats['is_balanced'] = False
    stats['duration_ms'] = int((time.perf_counter() - start) * 1000)
    
    print(f"\nMax cycles reached! Final gap: {final_gap:.2f} GWh")
    
    return stats

def run_full_recalc() -> Dict[str, Any]:
    """
    Centralized heavy recalculation invoked explicitly (e.g., from UI).
    Steps:
    - recalc all renewables once
    - recalc all Verbrauch rollups once
    - recalc WS data once
    Returns summary with timing and counts.
    """
    start = time.perf_counter()
    landuse_changes = []  # Track land use changes for display
    
    with transaction.atomic():
        lu_updates = 0
        for lu in LandUse.objects.all():
            # Store old values before recalculation
            old_target_ha = lu.target_ha
            old_user_percent = lu.user_percent
            
            before = RenewableData.objects.count()
            lu._recalculate_renewable_dependents()
            after = RenewableData.objects.count()
            lu_updates += max(after - before, 0)
            
            # Refresh from DB to get any updated values
            lu.refresh_from_db()
            
            # Track changes if target_ha changed
            if old_target_ha != lu.target_ha and lu.target_ha is not None:
                change_ha = (lu.target_ha or 0) - (old_target_ha or 0)
                if abs(change_ha) > 0.01:  # Only track significant changes (> 0.01 ha)
                    landuse_changes.append({
                        'code': lu.code,
                        'name': lu.name,
                        'old_percent': float(old_user_percent) if old_user_percent else None,
                        'new_percent': float(lu.user_percent) if lu.user_percent else None,
                        'old_ha': float(old_target_ha) if old_target_ha else None,
                        'new_ha': float(lu.target_ha) if lu.target_ha else None,
                        'change_ha': float(change_ha)
                    })
        
        renewables_updated = recalc_all_renewables_full()
        verbrauch_updated_codes: List[str] = recalc_all_verbrauch(trigger_code="manual")
        try:
            from simulator.renewable_recalc import recalc_renewables_for_verbrauch
            
            updated_from_verbrauch = 0
            for code in VerbrauchData.objects.values_list("code", flat=True):
                updated_codes = recalc_renewables_for_verbrauch(code)
                updated_from_verbrauch += len(updated_codes)
        except Exception:
            updated_from_verbrauch = 0
        from simulator.ws_365_service import get_ws_365_data
        get_ws_365_data(run_goal_seek=False)
            
    duration_ms = int((time.perf_counter() - start) * 1000)
    return {
        "duration_ms": duration_ms,
        "renewables_updated": renewables_updated,
        "verbrauch_updated": len(verbrauch_updated_codes),
        "renewables_from_verbrauch": updated_from_verbrauch,
        "landuse_driven_updates": lu_updates,
        "landuse_changes": landuse_changes,  # Include land use changes for tracking
    }
