"""WS 365 core calculations and goal-seek helpers."""

import math
import os
import logging
from typing import Optional

from .models import VerbrauchData, RenewableData
from .ws_models import WSData

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

logger = logging.getLogger(__name__)

GRID_LOSS_RATE = 0.092
ELECTROLYSIS_EFFICIENCY = 0.65
RUECKVERSTROEMUNG_EFFICIENCY = 0.585
FIXED_82_TARGET = 12000.0
MOBILE_GAP_TOLERANCE = 100.0
TOTAL_ENERGY_GAP_TOLERANCE = 100.0
PROCESS_GAP_TOLERANCE = 100.0
MOBILE_KNOB_STEP = 1.0
MOBILE_KNOB_MAX_JUMP = 20.0

def _validate_required_landuse(required_landuse: float, parent_target_ha: Optional[float], code: str) -> float:
    """
    Guard against corrupted/overflow land-use targets.
    """
    value = float(required_landuse or 0.0)
    if not math.isfinite(value):
        raise ValueError(f"{code} required landuse is not finite: {required_landuse}")
    if value < 0:
        raise ValueError(f"{code} required landuse is negative: {value}")
    if parent_target_ha and parent_target_ha > 0:
        max_allowed = float(parent_target_ha) * 100.0
        if value > max_allowed:
            raise ValueError(
                f"{code} required landuse too large ({value:,.2f} ha), max allowed {max_allowed:,.2f} ha"
            )
    return value

def get_ws_base_data():
    """Load WS inputs for 365 days (strictly the 4 input columns only)."""
    ws_entries = list(
        WSData.objects
        .filter(tag_im_jahr__gte=1, tag_im_jahr__lte=365)
        .only(
            'tag_im_jahr',
            'solar_promille',
            'wind_promille',
            'heizung_abwaerm_promille',
            'verbrauch_promille',
        )
        .order_by('tag_im_jahr')
    )
    
    return {
        'solar_promille': [ws.solar_promille or 0 for ws in ws_entries],
        'wind_promille': [ws.wind_promille or 0 for ws in ws_entries],
        'heizung_abwaerm_promille': [ws.heizung_abwaerm_promille or 0 for ws in ws_entries],
        'verbrauch_promille': [ws.verbrauch_promille or 0 for ws in ws_entries],
    }

def get_fixed_values():
    """Get fixed values from database."""
    verbrauch_7 = VerbrauchData.objects.get(code='7')
    verbrauch_7_ziel = verbrauch_7.ziel or 0
    verbrauch_292 = VerbrauchData.objects.get(code='2.9.2')
    verbrauch_24 = VerbrauchData.objects.get(code='2.4')
    verbrauch_292_ziel = verbrauch_292.ziel or 0
    verbrauch_24_ziel = verbrauch_24.ziel or 0
    
    r_911 = RenewableData.objects.get(code='9.1.1')
    r_912 = RenewableData.objects.get(code='9.1.2')
    r_913 = RenewableData.objects.get(code='9.1.3')
    r_914 = RenewableData.objects.get(code='9.1.4')
    r_92152 = RenewableData.objects.get(code='9.2.1.5.2')
    
    return {
        'verbrauch_7_ziel': verbrauch_7_ziel,
        'verbrauch_292_ziel': verbrauch_292_ziel,
        'verbrauch_24_ziel': verbrauch_24_ziel,
        'ziel_911': r_911.target_value or 0,  # Wind (fixed)
        'ziel_912': r_912.target_value or 0,  # Solar (variable)
        'ziel_913': r_913.target_value or 0,  # Sonst.
        'ziel_914': r_914.target_value or 0,  # Bio
        'ziel_92152': r_92152.target_value or 0,  # Subtraction
    }

def _calculate_365_days_legacy(solar_value, ws_data, fixed_values, wind_value=None):
    """
    Calculate all columns for 365 days given a Solar value.
    
    Args:
        solar_value: The solar generation value in GWh
        ws_data: Dictionary with promille arrays (from get_ws_base_data)
        fixed_values: Dictionary with fixed values (from get_fixed_values)
        wind_value: Optional wind override in GWh (defaults to fixed ziel_911)
    
    Returns:
        Dictionary with all results and daily data
    """
    solar_promille = ws_data['solar_promille']
    wind_promille = ws_data['wind_promille']
    heizung_abwaerm_promille = ws_data['heizung_abwaerm_promille']
    verbrauch_promille = ws_data['verbrauch_promille']
    
    ziel_911 = wind_value if wind_value is not None else fixed_values['ziel_911']
    ziel_912 = solar_value
    ziel_913 = fixed_values['ziel_913']
    ziel_914 = fixed_values['ziel_914']
    ziel_92152 = fixed_values['ziel_92152']
    
    annual_demand = fixed_values['verbrauch_7_ziel'] / (1 - GRID_LOSS_RATE)
    raumw_korr_annual = fixed_values['verbrauch_292_ziel'] * (fixed_values['verbrauch_24_ziel'] / 100)
    
    stromverbrauch = [annual_demand * verbrauch_promille[d] / 1000 for d in range(365)]
    davon_raumw_korr = [raumw_korr_annual * heizung_abwaerm_promille[d] / 365 for d in range(365)]
    stromverbr_raumw_korr = [stromverbrauch[d] + davon_raumw_korr[d] for d in range(365)]
    
    sum_renewable = ziel_911 + ziel_912 + ziel_913
    value = sum_renewable - ziel_92152
    pct = (value / sum_renewable) if sum_renewable > 0 else 0
    
    solar_strom = [ziel_912 * pct * solar_promille[d] / 1000 for d in range(365)]
    wind_strom = [ziel_911 * pct * wind_promille[d] / 1000 for d in range(365)]
    sonst_kraftw_daily = ziel_913 * pct / 365
    sonst_kraftw = [sonst_kraftw_daily for _ in range(365)]
    
    wind_solar_konstant = [solar_strom[d] + wind_strom[d] + sonst_kraftw[d] for d in range(365)]
    
    direktverbr_strom = [min(wind_solar_konstant[d], stromverbr_raumw_korr[d]) for d in range(365)]
    
    ueberschuss_strom = []
    for d in range(365):
        if direktverbr_strom[d] == stromverbr_raumw_korr[d]:
            ueberschuss_strom.append(wind_solar_konstant[d] - stromverbr_raumw_korr[d])
        else:
            ueberschuss_strom.append(0)
    
    einspeich = []
    for d in range(365):
        if stromverbr_raumw_korr[d] > 0:
            ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
        else:
            ratio = 0
        if ratio <= 1:
            einspeich.append(ueberschuss_strom[d] * ELECTROLYSIS_EFFICIENCY)
        else:
            einspeich.append(stromverbr_raumw_korr[d] * 1 * ELECTROLYSIS_EFFICIENCY)
    
    abregelung = []
    for d in range(365):
        if stromverbr_raumw_korr[d] > 0:
            ratio = ueberschuss_strom[d] / stromverbr_raumw_korr[d]
        else:
            ratio = 0
        if ratio <= 1:
            abregelung.append(0)
        else:
            abregelung.append(ueberschuss_strom[d] - einspeich[d] / ELECTROLYSIS_EFFICIENCY)
    
    mangel_last = [stromverbr_raumw_korr[d] - direktverbr_strom[d] for d in range(365)]
    
    mangel_last_total = sum(stromverbr_raumw_korr) - sum(direktverbr_strom)
    if mangel_last_total > 0:
        brennstoff_factor = ziel_914 / mangel_last_total
    else:
        brennstoff_factor = 0
    brennstoff_ausgleich = [brennstoff_factor * mangel_last[d] for d in range(365)]
    
    speicher_ausgl_strom = [mangel_last[d] - brennstoff_ausgleich[d] for d in range(365)]
    
    ausspeich_rueckverstr = [speicher_ausgl_strom[d] / RUECKVERSTROEMUNG_EFFICIENCY for d in range(365)]
    
    ausspeich_gas = [0 for _ in range(365)]
    
    ladezust_brutto = []
    for d in range(365):
        if d == 0:
            prev = 0
        else:
            prev = ladezust_brutto[d - 1]
        ladezust_brutto.append(prev + einspeich[d] - ausspeich_rueckverstr[d] - ausspeich_gas[d])

    min_ladezust_brutto = min(ladezust_brutto) if ladezust_brutto else 0
    ladezust_abs_vorl_tl = [lz - min_ladezust_brutto for lz in ladezust_brutto]

    selbstentl = [0 for _ in range(365)]

    ladezust_netto = []
    for d in range(365):
        if d == 0:
            prev_netto = 0
        else:
            prev_netto = ladezust_netto[d - 1]
        ladezust_netto.append(
            prev_netto
            + einspeich[d]
            - ausspeich_rueckverstr[d]
            - ausspeich_gas[d]
            - selbstentl[d]
        )

    min_ladezust_netto = min(ladezust_netto) if ladezust_netto else 0
    ladezust_absolute = [lz - min_ladezust_netto for lz in ladezust_netto]
    
    base_electricity = ziel_911 + ziel_912 + ziel_913 - ziel_92152
    einspeich_adjustment = sum(einspeich) / ELECTROLYSIS_EFFICIENCY
    abregelung_total = sum(abregelung)
    ausspeich_rueckverstr_adjustment = sum(ausspeich_rueckverstr) * RUECKVERSTROEMUNG_EFFICIENCY
    annual_electricity = base_electricity - einspeich_adjustment - abregelung_total + ziel_914 + ausspeich_rueckverstr_adjustment
    
    daily_data = []
    for d in range(365):
        daily_data.append({
            'day': d + 1,
            'solar_promille': solar_promille[d],
            'wind_promille': wind_promille[d],
            'heizung_abwaerm_promille': heizung_abwaerm_promille[d],
            'verbrauch_promille': verbrauch_promille[d],
            'stromverbrauch': round(stromverbrauch[d], 2),
            'davon_raumw_korr': round(davon_raumw_korr[d], 2),
            'stromverbr_raumw_korr': round(stromverbr_raumw_korr[d], 2),
            'solar_strom': round(solar_strom[d], 2),
            'wind_strom': round(wind_strom[d], 2),
            'sonst_kraftw': round(sonst_kraftw[d], 2),
            'wind_solar_konstant': round(wind_solar_konstant[d], 2),
            'direktverbr_strom': round(direktverbr_strom[d], 2),
            'ueberschuss_strom': round(ueberschuss_strom[d], 2),
            'einspeich': round(einspeich[d], 2),
            'abregelung': round(abregelung[d], 2),
            'mangel_last': round(mangel_last[d], 2),
            'brennstoff_ausgleich': round(brennstoff_ausgleich[d], 2),
            'speicher_ausgl_strom': round(speicher_ausgl_strom[d], 2),
            'ausspeich_rueckverstr': round(ausspeich_rueckverstr[d], 2),
            'ausspeich_gas': round(ausspeich_gas[d], 2),
            'ladezust_brutto': round(ladezust_brutto[d], 2),
            'ladezust_abs_vorl_tl': round(ladezust_abs_vorl_tl[d], 2),
            'selbstentl': round(selbstentl[d], 2),
            'ladezust_netto': round(ladezust_netto[d], 2),
            'ladezust_absolute': round(ladezust_absolute[d], 2),
        })
    
    return {
        'ladezust_day1': ladezust_brutto[0],
        'ladezust_day365': ladezust_brutto[364],
        'annual_electricity': annual_electricity,
        'annual_demand': annual_demand,
        'storage_drift': ladezust_brutto[364] - ladezust_brutto[0],
        'einspeich_sum': sum(einspeich),
        'ausspeich_sum': sum(ausspeich_rueckverstr),
        'abregelung_sum': sum(abregelung),
        'ueberschuss_sum': sum(ueberschuss_strom),
        'solar_strom_sum': sum(solar_strom),
        'wind_strom_sum': sum(wind_strom),
        'renewable_pct': pct * 100,
        'daily_data': daily_data,
    }

def calculate_365_days(solar_value, ws_data, fixed_values, wind_value=None):
    """
    Calculate WS 365-day outputs.

    Primary path: DB-driven WS365Formula engine (admin-editable).
    Fallback path: legacy hardcoded Python formulas for safety.
    """
    try:
        from .ws365_formula_engine import calculate_365_days_with_formulas

        return calculate_365_days_with_formulas(
            solar_value=solar_value,
            ws_data=ws_data,
            fixed_values=fixed_values,
            grid_loss_rate=GRID_LOSS_RATE,
            eta_strom_gas=ELECTROLYSIS_EFFICIENCY,
            eta_gas_strom=RUECKVERSTROEMUNG_EFFICIENCY,
            wind_value=wind_value,
        )
    except RuntimeError:
        return _calculate_365_days_legacy(solar_value, ws_data, fixed_values, wind_value=wind_value)
    except Exception as exc:
        logger.error("WS DB formula engine failed, using legacy fallback: %s", exc)
        return _calculate_365_days_legacy(solar_value, ws_data, fixed_values, wind_value=wind_value)

def goal_seek_optimal_solar(ws_data, fixed_values, tolerance=0.1, max_iterations=50):
    """
    Find optimal Solar value where storage_drift ≈ 0 (Day 365 = Day 1).
    
    Args:
        ws_data: Dictionary with promille arrays
        fixed_values: Dictionary with fixed values
        tolerance: Acceptable storage drift in GWh
        max_iterations: Maximum binary search iterations
    
    Returns:
        Dictionary with optimal solar value and results
    """
    original_solar = fixed_values['ziel_912']
    solar_low = original_solar * 0.5
    solar_high = original_solar * 1.5
    
    for iteration in range(max_iterations):
        solar_mid = (solar_low + solar_high) / 2
        result = calculate_365_days(solar_mid, ws_data, fixed_values)
        drift = result['storage_drift']
        
        if abs(drift) < tolerance:
            break
        
        if drift > 0:
            solar_high = solar_mid
        else:
            solar_low = solar_mid
    
    optimal_result = calculate_365_days(solar_mid, ws_data, fixed_values)
    
    return {
        'original_solar': original_solar,
        'optimal_solar': solar_mid,
        'solar_change': solar_mid - original_solar,
        'solar_change_pct': ((solar_mid / original_solar) - 1) * 100 if original_solar > 0 else 0,
        'iterations': iteration + 1,
        'result': optimal_result,
    }

def goal_seek_optimal_wind(ws_data, fixed_values, tolerance=0.1, max_iterations=50):
    """
    Find optimal Wind value where storage_drift ≈ 0 (Day 365 = Day 1),
    keeping Solar fixed.
    """
    original_wind = max(0.0, float(fixed_values.get('ziel_911') or 0.0))

    def _evaluate(wind_candidate):
        result = calculate_365_days(
            fixed_values['ziel_912'],
            ws_data,
            fixed_values,
            wind_value=wind_candidate
        )
        return float(result['storage_drift']), result

    base_wind = max(original_wind, 1.0)
    wind_low = max(0.0, base_wind * 0.5)
    wind_high = max(base_wind * 1.5, wind_low + 1.0)

    drift_low, result_low = _evaluate(wind_low)
    drift_high, result_high = _evaluate(wind_high)

    expansion_steps = 0
    max_expansion_steps = 12
    while drift_low * drift_high > 0 and expansion_steps < max_expansion_steps:
        expansion_steps += 1

        if drift_low < 0 and drift_high < 0:
            # Need more Wind to move drift upward through zero.
            wind_low, drift_low, result_low = wind_high, drift_high, result_high
            wind_high = max(wind_high * 1.7, wind_high + 1.0)
            drift_high, result_high = _evaluate(wind_high)
        elif drift_low > 0 and drift_high > 0:
            # Need less Wind to move drift downward through zero.
            wind_high, drift_high, result_high = wind_low, drift_low, result_low
            if wind_low <= 0:
                break
            wind_low = max(0.0, wind_low * 0.3)
            drift_low, result_low = _evaluate(wind_low)
        else:
            break

    if drift_low * drift_high > 0:
        if abs(drift_low) <= abs(drift_high):
            optimal_wind, optimal_result = wind_low, result_low
        else:
            optimal_wind, optimal_result = wind_high, result_high
        return {
            'original_wind': original_wind,
            'optimal_wind': optimal_wind,
            'wind_change': optimal_wind - original_wind,
            'wind_change_pct': ((optimal_wind / original_wind) - 1) * 100 if original_wind > 0 else 0,
            'iterations': expansion_steps + 1,
            'result': optimal_result,
        }

    # Standard bisection within sign-changing bracket.
    wind_mid = (wind_low + wind_high) / 2.0
    optimal_result = result_low
    bisection_iterations = 0

    for iteration in range(max_iterations):
        bisection_iterations = iteration + 1
        wind_mid = (wind_low + wind_high) / 2.0
        drift_mid, result_mid = _evaluate(wind_mid)
        optimal_result = result_mid

        if abs(drift_mid) < tolerance:
            break

        if drift_low * drift_mid <= 0:
            wind_high = wind_mid
            drift_high = drift_mid
        else:
            wind_low = wind_mid
            drift_low = drift_mid

    return {
        'original_wind': original_wind,
        'optimal_wind': wind_mid,
        'wind_change': wind_mid - original_wind,
        'wind_change_pct': ((wind_mid / original_wind) - 1) * 100 if original_wind > 0 else 0,
        'iterations': expansion_steps + bisection_iterations,
        'result': optimal_result,
    }

def update_renewable_from_ws365(ws_result):
    """
    Update RenewableData 9.3.1 and 9.3.4 target values from WS 365 calculation.
    
    This ensures all dependent formulas (9.3.1.2, 9.3.1.3, etc.) will use 
    the correct WS 365 values when they are calculated.
    
    Args:
        ws_result: Result dictionary from calculate_365_days()
    """
    # 9.3.1 ziel = einspeich_sum / 0.65
    einspeich_sum = ws_result.get('einspeich_sum', 0)
    value_931 = einspeich_sum / ELECTROLYSIS_EFFICIENCY if einspeich_sum > 0 else 0
    
    # 9.3.4 ziel = abregelung_sum
    value_934 = ws_result.get('abregelung_sum', 0)
    
    try:
        r931 = RenewableData.objects.get(code='9.3.1')
        if r931.target_value != value_931:
            r931.target_value = value_931
            r931.save(skip_cascade=True, update_fields=['target_value'])
            print(f"Updated 9.3.1 ziel to {value_931:.2f} GWh")
    except RenewableData.DoesNotExist:
        print("RenewableData 9.3.1 not found")
    
    try:
        r934 = RenewableData.objects.get(code='9.3.4')
        if r934.target_value != value_934:
            r934.target_value = value_934
            r934.save(skip_cascade=True, update_fields=['target_value'])
            print(f"Updated 9.3.4 ziel to {value_934:.2f} GWh")
    except RenewableData.DoesNotExist:
        print("RenewableData 9.3.4 not found")

def calculate_required_landuse(optimal_solar):
    """
    Reverse-engineer the LandUse (LU_2.1) needed to achieve the optimal Solar value.
    
    The formula chain is:
    - 9.1.2 = 1.1.2.1.2 + 1.2.1.2
    - 1.2.1.2 = LU_2.1 * 1.2.1.1 / 1000
    
    So: LU_2.1 = (optimal_solar - 1.1.2.1.2) * 1000 / 1.2.1.1
    
    Args:
        optimal_solar: The optimal Solar (9.1.2) value in GWh
    
    Returns:
        dict with required_landuse (ha) and other info
    """
    from .models import LandUse
    
    # Get current values
    r_11212 = RenewableData.objects.get(code='1.1.2.1.2')
    r_1211 = RenewableData.objects.get(code='1.2.1.1')
    lu_21 = LandUse.objects.get(code='LU_2.1')
    
    fixed_solar = r_11212.target_value or 0  # 1.1.2.1.2 (Rooftop PV - not from LU_2.1)
    yield_factor = r_1211.target_value or 1  # 1.2.1.1 (yield per ha)
    current_landuse = lu_21.target_ha or 0
    
    required_1212 = optimal_solar - fixed_solar
    required_landuse = required_1212 * 1000 / yield_factor if yield_factor > 0 else 0
    
    return {
        'optimal_solar': optimal_solar,
        'fixed_solar': fixed_solar,
        'required_1212': required_1212,
        'yield_factor': yield_factor,
        'required_landuse': required_landuse,
        'current_landuse': current_landuse,
        'landuse_change': required_landuse - current_landuse,
    }

def calculate_required_landuse_wind(optimal_wind):
    """
    Reverse-engineer LandUse (LU_6) needed to achieve optimal Wind (9.1.1).

    Chain:
    - 9.1.1 = 2.2.1.2.3 + 2.1.1.2.2
    - 2.1.1.2.2 = (2.1.1 / 2.1.1.1) * 2.1.1.2.1 / 1000
    - 2.1.1 = LU_6
    """
    from .models import LandUse

    r_22123 = RenewableData.objects.get(code='2.2.1.2.3')
    r_21111 = RenewableData.objects.get(code='2.1.1.1')
    r_211121 = RenewableData.objects.get(code='2.1.1.2.1')
    lu_6 = LandUse.objects.get(code='LU_6')

    fixed_wind = r_22123.target_value or 0  # non-LU_6 wind component
    factor_21111 = r_21111.target_value or 0
    factor_211121 = r_211121.target_value or 0
    current_landuse = lu_6.target_ha or 0

    required_211122 = optimal_wind - fixed_wind
    if factor_211121 > 0:
        required_landuse = required_211122 * 1000 * factor_21111 / factor_211121
    else:
        required_landuse = 0

    return {
        'optimal_wind': optimal_wind,
        'fixed_wind': fixed_wind,
        'required_211122': required_211122,
        'factor_21111': factor_21111,
        'factor_211121': factor_211121,
        'required_landuse': required_landuse,
        'current_landuse': current_landuse,
        'landuse_change': required_landuse - current_landuse,
    }
