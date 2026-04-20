"""WS 365 sector-balancing helpers."""

import os

from .models import VerbrauchData, RenewableData
from .ws365_core import (
    FIXED_82_TARGET,
    MOBILE_GAP_TOLERANCE,
    MOBILE_KNOB_MAX_JUMP,
    MOBILE_KNOB_STEP,
    PROCESS_GAP_TOLERANCE,
)

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

def _get_sector_totals():
    """
    Read the live sector totals used by the active pages:
    - Demand: Verbrauch 2.10 (Gebäudewärme), 3.7 (Prozesswärme)
    - Supply: Renewable 10.4 (Gebäudewärme), 10.5 (Prozesswärme)
    - Mobile fuel: Verbrauch 6.1 (demand) vs Renewable 10.6.1 (supply)
    - Optional total energy: Verbrauch 7 vs Renewable 10.1
    """
    v210 = VerbrauchData.objects.get(code='2.10')
    v37 = VerbrauchData.objects.get(code='3.7')
    v61 = VerbrauchData.objects.get(code='6.1')
    r104 = RenewableData.objects.get(code='10.4')
    r105 = RenewableData.objects.get(code='10.5')
    r1061 = RenewableData.objects.get(code='10.6.1')

    gw_demand = float(v210.ziel or 0)
    pw_demand = float(v37.ziel or 0)
    mobile_demand = float(v61.ziel or 0)
    gw_supply = float(r104.target_value or 0)
    pw_supply = float(r105.target_value or 0)
    mobile_supply = float(r1061.target_value or 0)

    totals = {
        'gebaeudewaerme': {
            'demand': gw_demand,
            'supply': gw_supply,
            'gap': gw_demand - gw_supply,
        },
        'prozesswaerme': {
            'demand': pw_demand,
            'supply': pw_supply,
            'gap': pw_demand - pw_supply,
        },
        'mobile_anwendungen': {
            'demand': mobile_demand,
            'supply': mobile_supply,
            'gap': mobile_demand - mobile_supply,
        },
    }

    try:
        v7 = VerbrauchData.objects.get(code='7')
        r101 = RenewableData.objects.get(code='10.1')
        total_demand = float(v7.ziel or 0)
        total_supply = float(r101.target_value or 0)
        totals['total_energy'] = {
            'demand': total_demand,
            'supply': total_supply,
            'gap': total_demand - total_supply,
        }
    except (VerbrauchData.DoesNotExist, RenewableData.DoesNotExist):
        pass

    return totals

def _balance_heat_sectors_after_ws():
    """
    After electricity/WS balancing, align sector totals:
    - Gebäudewärme: 10.4 (supply) to 2.10 (demand) via Verbrauch 2.8 ziel
    - Prozesswärme: 10.5 (supply) to 3.7 (demand) via Verbrauch 3.4 ziel (%)
    - Mobile Anwendungen (fuel): 10.6.1 (supply) to 6.1 (demand)
      primary knob Verbrauch 4.1.2.6 ziel, secondary knob Verbrauch 4.1.1.6 ziel

    Returns detailed before/after values for API/UI visibility.
    """
    from simulator.recalc_service import recalc_all_renewables_full
    from simulator.verbrauch_recalculator import recalc_all_verbrauch

    # Keep 8.2 fixed to the required baseline value.
    r82_fixed = RenewableData.objects.get(code='8.2')
    old_82_target = float(r82_fixed.target_value or 0)
    if abs(old_82_target - FIXED_82_TARGET) > 1e-9:
        r82_fixed.target_value = FIXED_82_TARGET
        r82_fixed.is_fixed = True
        r82_fixed.save(skip_cascade=True, update_fields=['target_value', 'is_fixed'])
    new_82_target = float(r82_fixed.target_value or 0)

    def settle_totals(trigger_prefix: str, max_rounds: int = 3, tolerance: float = 1.0):
        """
        Recalculate until heat-sector gaps stabilize.
        This avoids optimizing 2.8 against transient intermediate states.
        """
        prev = None
        current = None
        for idx in range(max_rounds):
            recalc_all_verbrauch(trigger_code=f"{trigger_prefix}_{idx + 1}")
            recalc_all_renewables_full(exclude_ws_dependent=False)
            current = _get_sector_totals()
            if prev is not None:
                gw_delta = abs(current['gebaeudewaerme']['gap'] - prev['gebaeudewaerme']['gap'])
                pw_delta = abs(current['prozesswaerme']['gap'] - prev['prozesswaerme']['gap'])
                mobile_delta = abs(current['mobile_anwendungen']['gap'] - prev['mobile_anwendungen']['gap'])
                if gw_delta <= tolerance and pw_delta <= tolerance and mobile_delta <= tolerance:
                    break
            prev = current
        return current or _get_sector_totals()

    before = settle_totals("ws_heat_balance_start")

    # --- Gebäudewärme knob: Verbrauch 2.8 ziel (%) ---
    v28 = VerbrauchData.objects.get(code='2.8')
    old_28 = float(v28.ziel or 0)
    old_gap = float(before['gebaeudewaerme']['gap'])
    best_28 = old_28
    best_gap = abs(old_gap)
    tried_points = [(old_28, old_gap)]

    def _clamp_28(value_28: float) -> float:
        return max(0.0, min(100.0, float(value_28)))

    def apply_28_and_get_gap(value_28: float, settle_rounds: int = 3):
        value_28 = _clamp_28(value_28)
        v28.ziel = value_28
        if v28.user_editable:
            v28.user_percent = value_28
            v28.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel', 'user_percent']
            )
        else:
            v28.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel']
            )

        settled = settle_totals("ws_heat_balance_2_8", max_rounds=max(1, settle_rounds))
        gap_now = float(settled['gebaeudewaerme']['gap'])
        return value_28, gap_now, settled

    def _remember_candidate(x_val: float, gap_val: float):
        nonlocal best_28, best_gap
        tried_points.append((x_val, gap_val))
        if abs(gap_val) < best_gap:
            best_gap = abs(gap_val)
            best_28 = x_val

    def _evaluate_28_gap(value_28: float, settle_rounds: int = 3):
        """
        Evaluate a real committed state for 2.8 and return the resulting gap.
        """
        x_eval, g_eval, _ = apply_28_and_get_gap(value_28, settle_rounds=settle_rounds)
        _remember_candidate(x_eval, g_eval)
        return x_eval, g_eval

    gw_gap_tolerance = 100.0

    if abs(old_gap) > gw_gap_tolerance:
        x_curr = old_28
        g_curr = old_gap
        probe_step = 0.5

        for _ in range(6):
            if abs(g_curr) <= gw_gap_tolerance:
                break

            direction = -1.0 if g_curr > 0 else 1.0
            x_probe = _clamp_28(x_curr + (direction * probe_step))
            if abs(x_probe - x_curr) < 1e-9:
                break

            x_probe, g_probe = _evaluate_28_gap(x_probe, settle_rounds=3)

            slope = None
            if abs(x_probe - x_curr) > 1e-9:
                slope = (g_probe - g_curr) / (x_probe - x_curr)

            x_next = None
            g_next = None
            if slope is not None and abs(slope) > 1e-9:
                x_guess = _clamp_28(x_curr - (g_curr / slope))
                max_jump = max(1.0, probe_step * 4.0)
                x_guess = max(x_curr - max_jump, min(x_curr + max_jump, x_guess))
                if abs(x_guess - x_probe) > 1e-9 and abs(x_guess - x_curr) > 1e-9:
                    x_next, g_next = _evaluate_28_gap(x_guess, settle_rounds=3)

            candidates = [(x_curr, g_curr), (x_probe, g_probe)]
            if x_next is not None:
                candidates.append((x_next, g_next))

            target_x, _ = min(candidates, key=lambda item: abs(item[1]))
            current_state_x = candidates[-1][0]

            if abs(target_x - current_state_x) > 1e-9:
                target_x, target_gap, _ = apply_28_and_get_gap(target_x, settle_rounds=3)
                _remember_candidate(target_x, target_gap)
            else:
                target_gap = candidates[-1][1]

            improved = abs(target_gap) < abs(g_curr)
            x_curr, g_curr = target_x, target_gap

            if improved:
                probe_step = min(2.0, probe_step * 1.3)
            else:
                probe_step = max(0.1, probe_step * 0.5)
                if probe_step <= 0.11:
                    break

    v28.refresh_from_db(fields=['ziel', 'user_percent'])
    final_28, final_gw_gap, totals_after_28 = apply_28_and_get_gap(best_28, settle_rounds=3)

    v34 = VerbrauchData.objects.get(code='3.4')
    v35 = VerbrauchData.objects.get(code='3.5')
    v343 = VerbrauchData.objects.get(code='3.4.3')
    r1022 = RenewableData.objects.get(code='10.2.2')
    r1051 = RenewableData.objects.get(code='10.5.1')
    r1052 = RenewableData.objects.get(code='10.5.2')

    old_34 = float(v34.ziel or 0)
    old_pw_gap = float(totals_after_28['prozesswaerme']['gap'])

    v35_ziel = float(v35.ziel or 0)
    v343_ziel = float(v343.ziel or 0)
    denom_36 = 1.0 + (v343_ziel / 100.0)
    if abs(denom_36) < 1e-9:
        denom_36 = 1e-9
    max_34_from_36 = (100.0 - v35_ziel) / denom_36
    min_34 = 0.0
    max_34 = max(min_34, min(100.0, max_34_from_36))

    process_adjustment = {
        'knob': 'Verbrauch 3.4',
        'old_3_4_percent': old_34,
        'new_3_4_percent': old_34,
        'min_3_4_percent': min_34,
        'max_3_4_percent': max_34,
        'old_pw_gap': old_pw_gap,
        'new_pw_gap': old_pw_gap,
        'delta_percent': 0.0,
        'applied': False,
        'iterations': 0,
        'reason': '',
    }

    def _clamp_34(value_34: float) -> float:
        return max(min_34, min(max_34, float(value_34)))

    def _apply_34_and_settle(value_34: float, settle_rounds: int = 2):
        """Apply 3.4 once, then run controlled recalc rounds to settle totals."""
        value_34 = _clamp_34(value_34)
        v34.ziel = value_34
        if v34.user_editable:
            v34.user_percent = value_34
            v34.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel', 'user_percent']
            )
        else:
            v34.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel']
            )
        settled_now = settle_totals("ws_heat_balance_3_4_direct", max_rounds=max(1, settle_rounds), tolerance=1.0)
        pw_gap_now = float(settled_now['prozesswaerme']['gap'])
        v36_now = float(VerbrauchData.objects.get(code='3.6').ziel or 0)
        return value_34, pw_gap_now, settled_now, v36_now

    pw_gap_tolerance = PROCESS_GAP_TOLERANCE
    process_evals = 0
    process_reason = 'PW gap already within tolerance'
    final_34 = old_34
    final_pw_gap = old_pw_gap

    if abs(old_pw_gap) > pw_gap_tolerance:
        v33_ziel = float(VerbrauchData.objects.get(code='3.3').ziel or 0)
        k_1022 = float(r1022.target_value or 0) / 100.0
        const_105 = float(r1051.target_value or 0) + float(r1052.target_value or 0)
        q_343 = v343_ziel / 100.0

        const_term = (
            v33_ziel
            - const_105
            - (k_1022 * v33_ziel * (100.0 - v35_ziel) / 100.0)
        )
        slope_term = (v33_ziel / 100.0) * ((k_1022 * (1.0 + q_343)) - q_343)

        if abs(slope_term) > 1e-9:
            direct_34 = _clamp_34(-const_term / slope_term)
            final_34, final_pw_gap, _, v36_after = _apply_34_and_settle(direct_34, settle_rounds=2)
            process_evals += 1
            process_reason = 'Direct closed-form 3.4 solve'

            if (
                abs(final_pw_gap) > pw_gap_tolerance and
                abs(final_34 - old_34) > 1e-9 and
                abs(final_pw_gap - old_pw_gap) > 1e-9
            ):
                corrected_34 = _clamp_34(
                    final_34 - final_pw_gap * (final_34 - old_34) / (final_pw_gap - old_pw_gap)
                )
                final_34, final_pw_gap, _, v36_after = _apply_34_and_settle(corrected_34, settle_rounds=2)
                process_evals += 1
                process_reason = 'Direct closed-form 3.4 solve + one correction'

            if v36_after < 0:
                safe_34 = _clamp_34((100.0 - v35_ziel) / denom_36)
                final_34, final_pw_gap, _, _ = _apply_34_and_settle(safe_34, settle_rounds=2)
                process_evals += 1
                process_reason = 'Adjusted to safe 3.6>=0 bound after direct solve'
        else:
            process_reason = 'Direct solve slope near zero; kept existing 3.4'

    process_adjustment.update({
        'new_3_4_percent': final_34,
        'new_pw_gap': final_pw_gap,
        'delta_percent': final_34 - old_34,
        'applied': abs(final_34 - old_34) > 1e-9,
        'iterations': process_evals,
        'reason': (
            'PW gap already within tolerance'
            if abs(old_pw_gap) <= pw_gap_tolerance
            else (process_reason or 'No change needed')
        ),
    })

    # Recalculate until stable after heat knob updates.
    post_heat = settle_totals("ws_heat_balance_final")

    mobile_before = post_heat['mobile_anwendungen']
    mobile_gap_before = float(mobile_before['gap'])

    v4116 = VerbrauchData.objects.get(code='4.1.1.6')
    v4126 = VerbrauchData.objects.get(code='4.1.2.6')
    old_4116 = float(v4116.ziel or 0)
    old_4126 = float(v4126.ziel or 0)

    def _clamp_percent(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _set_percent_knob(item: VerbrauchData, new_value: float):
        new_value = _clamp_percent(new_value)
        item.user_percent = new_value
        if item.user_editable:
            item.save(skip_rebalance=True)
        else:
            item.ziel = new_value
            item.save(
                skip_cascade=True,
                skip_rebalance=True,
                update_fields=['ziel']
            )
        return new_value

    def _apply_mobile_knobs_and_get_gap(value_4116: float, value_4126: float, settle_rounds: int = 1):
        value_4116 = _set_percent_knob(v4116, value_4116)
        value_4126 = _set_percent_knob(v4126, value_4126)
        settled = settle_totals(
            "ws_heat_balance_mobile_knobs",
            max_rounds=max(1, settle_rounds),
            tolerance=1.0
        )
        gap_now = float(settled['mobile_anwendungen']['gap'])
        return value_4116, value_4126, gap_now, settled

    current_4116 = old_4116
    current_4126 = old_4126
    current_gap = mobile_gap_before

    mobile_primary_adjustment = {
        'knob': 'Verbrauch 4.1.2.6',
        'old_percent': old_4126,
        'new_percent': old_4126,
        'delta_percent': 0.0,
        'old_gap': mobile_gap_before,
        'new_gap': mobile_gap_before,
        'applied': False,
        'iterations': 0,
        'reason': '',
    }

    if abs(current_gap) > MOBILE_GAP_TOLERANCE:
        primary_candidates = [(current_4126, current_gap)]
        eval_count = 0
        reason = 'Primary knob at bound'

        probe_dir = 1.0 if current_4126 <= (100.0 - MOBILE_KNOB_STEP) else -1.0
        probe_4126 = _clamp_percent(current_4126 + (probe_dir * MOBILE_KNOB_STEP))
        if abs(probe_4126 - current_4126) > 1e-9:
            current_4116, current_4126, probe_gap, _ = _apply_mobile_knobs_and_get_gap(
                current_4116,
                probe_4126,
                settle_rounds=1
            )
            eval_count += 1
            primary_candidates.append((current_4126, probe_gap))
            reason = 'Primary knob probe applied'

            slope = (probe_gap - mobile_gap_before) / (probe_4126 - old_4126)
            if abs(slope) > 1e-9:
                guess_4126 = _clamp_percent(old_4126 - (mobile_gap_before / slope))
                guess_4126 = max(
                    old_4126 - MOBILE_KNOB_MAX_JUMP,
                    min(old_4126 + MOBILE_KNOB_MAX_JUMP, guess_4126)
                )
                if abs(guess_4126 - current_4126) > 1e-9:
                    current_4116, current_4126, guess_gap, _ = _apply_mobile_knobs_and_get_gap(
                        current_4116,
                        guess_4126,
                        settle_rounds=1
                    )
                    eval_count += 1
                    primary_candidates.append((current_4126, guess_gap))
                    reason = 'Primary direct solve applied'

                    # One deterministic correction step.
                    if abs(guess_gap) > MOBILE_GAP_TOLERANCE and abs(guess_gap - probe_gap) > 1e-9:
                        correction_4126 = _clamp_percent(
                            current_4126 - guess_gap * (current_4126 - probe_4126) / (guess_gap - probe_gap)
                        )
                        if abs(correction_4126 - current_4126) > 1e-9:
                            current_4116, current_4126, corr_gap, _ = _apply_mobile_knobs_and_get_gap(
                                current_4116,
                                correction_4126,
                                settle_rounds=1
                            )
                            eval_count += 1
                            primary_candidates.append((current_4126, corr_gap))
                            reason = 'Primary direct solve + one correction'
            else:
                reason = 'Primary knob sensitivity near zero'

        best_4126, best_gap = min(primary_candidates, key=lambda item: abs(item[1]))
        if abs(best_4126 - current_4126) > 1e-9:
            current_4116, current_4126, best_gap, _ = _apply_mobile_knobs_and_get_gap(
                current_4116,
                best_4126,
                settle_rounds=1
            )
            eval_count += 1

        current_gap = best_gap
        mobile_primary_adjustment.update({
            'new_percent': current_4126,
            'delta_percent': current_4126 - old_4126,
            'new_gap': current_gap,
            'applied': abs(current_4126 - old_4126) > 1e-9,
            'iterations': eval_count,
            'reason': reason,
        })
    else:
        mobile_primary_adjustment['reason'] = 'Mobile gap already within tolerance'

    mobile_secondary_adjustment = {
        'knob': 'Verbrauch 4.1.1.6',
        'old_percent': old_4116,
        'new_percent': old_4116,
        'delta_percent': 0.0,
        'old_gap': current_gap,
        'new_gap': current_gap,
        'applied': False,
        'iterations': 0,
        'reason': '',
    }

    primary_improved = abs(current_gap) < (abs(mobile_gap_before) - 1.0)

    if abs(current_gap) > MOBILE_GAP_TOLERANCE and not primary_improved:
        eval_count = 0
        reason = 'Secondary knob at bound'
        probe_dir = 1.0 if current_4116 <= (100.0 - MOBILE_KNOB_STEP) else -1.0
        probe_4116 = _clamp_percent(current_4116 + (probe_dir * MOBILE_KNOB_STEP))

        if abs(probe_4116 - current_4116) > 1e-9:
            base_gap = current_gap
            base_4116 = current_4116
            secondary_candidates = [(base_4116, base_gap)]
            current_4116, current_4126, probe_gap, _ = _apply_mobile_knobs_and_get_gap(
                probe_4116,
                current_4126,
                settle_rounds=1
            )
            eval_count += 1
            secondary_candidates.append((current_4116, probe_gap))
            reason = 'Secondary knob probe applied'

            slope = (probe_gap - base_gap) / (probe_4116 - base_4116)
            if abs(slope) > 1e-9:
                guess_4116 = _clamp_percent(base_4116 - (base_gap / slope))
                guess_4116 = max(
                    base_4116 - MOBILE_KNOB_MAX_JUMP,
                    min(base_4116 + MOBILE_KNOB_MAX_JUMP, guess_4116)
                )
                if abs(guess_4116 - current_4116) > 1e-9:
                    current_4116, current_4126, guess_gap, _ = _apply_mobile_knobs_and_get_gap(
                        guess_4116,
                        current_4126,
                        settle_rounds=1
                    )
                    eval_count += 1
                    secondary_candidates.append((current_4116, guess_gap))
                    reason = 'Secondary direct solve applied'
            else:
                reason = 'Secondary knob sensitivity near zero'

            best_4116, best_gap = min(secondary_candidates, key=lambda item: abs(item[1]))
            if abs(best_4116 - current_4116) > 1e-9:
                current_4116, current_4126, best_gap, _ = _apply_mobile_knobs_and_get_gap(
                    best_4116,
                    current_4126,
                    settle_rounds=1
                )
                eval_count += 1
            current_gap = best_gap

        mobile_secondary_adjustment.update({
            'new_percent': current_4116,
            'delta_percent': current_4116 - old_4116,
            'new_gap': current_gap,
            'applied': abs(current_4116 - old_4116) > 1e-9,
            'iterations': eval_count,
            'reason': reason,
        })
    else:
        mobile_secondary_adjustment['reason'] = (
            'No secondary adjustment needed after primary knob'
            if abs(current_gap) <= MOBILE_GAP_TOLERANCE
            else 'Primary knob already improved gap; secondary skipped'
        )

    # Final settle with the selected knob values.
    current_4116, current_4126, current_gap, after = _apply_mobile_knobs_and_get_gap(
        current_4116,
        current_4126,
        settle_rounds=1
    )
    mobile_primary_adjustment['new_gap'] = current_gap
    mobile_secondary_adjustment['new_gap'] = current_gap

    return {
        'before': before,
        'post_heat': post_heat,
        'after': after,
        'adjustments': {
            'verbrauch_2_8': {
                'old_ziel_percent': old_28,
                'new_ziel_percent': final_28,
                'delta_percent': final_28 - old_28,
                'final_gap': after['gebaeudewaerme']['gap'],
                'applied': abs(final_28 - old_28) > 1e-9,
            },
            'renewable_8_2_fixed': {
                'old_target': old_82_target,
                'new_target': new_82_target,
                'fixed_target': FIXED_82_TARGET,
                'applied': abs(old_82_target - new_82_target) > 1e-9,
            },
            'verbrauch_3_4': process_adjustment,
            'verbrauch_4_1_2_6_mobile_primary': mobile_primary_adjustment,
            'verbrauch_4_1_1_6_mobile_secondary': mobile_secondary_adjustment,
        },
    }

