"""Candidate direct-solve for the GW 2.8 knob.

Step 2.1 candidate — NOT YET wired into production. Used by the shadow-parity
test to prove (or disprove) that a 1-shot linear solve produces the same
result as the existing 6-iteration secant in ws365_sector_balance.py.

The claim: every formula touching Verbrauch_2.8 is a linear weighted sum, so
gap_gw(x_28) = a*x + b for real coefficients a, b. A 2-point probe gives the
exact slope, and one Newton step lands on gap=0 (within numerical noise).
One correction step handles any noise.

The safety gate is external: run this alongside the secant for synthetic
imbalances and assert agreement before flipping any production switch.
"""
from typing import Callable, Tuple


def solve_gw_2_8_direct(
    old_28: float,
    old_gap: float,
    evaluate: Callable[[float], Tuple[float, float]],
    clamp: Callable[[float], float],
    gap_tolerance: float = 100.0,
    probe_step: float = 0.5,
    max_correction_jump: float = 10.0,
) -> Tuple[float, float, int]:
    """Candidate direct-solve. Returns (best_28, best_gap, eval_count).

    Strategy:
      1. If gap already within tolerance, return immediately.
      2. Probe at old_28 ± probe_step → estimates slope.
      3. Newton step: x_new = old_28 - old_gap / slope; clamp to [0, 100].
      4. Evaluate at x_new. If within tolerance, done.
      5. Optional correction: one more secant step using last two points.
    """
    eval_count = 0

    if abs(old_gap) <= gap_tolerance:
        return old_28, old_gap, 0

    # Probe direction based on sign of gap
    direction = -1.0 if old_gap > 0 else 1.0
    x_probe = clamp(old_28 + direction * probe_step)
    if abs(x_probe - old_28) < 1e-9:
        # old_28 is at a bound; try the other direction
        x_probe = clamp(old_28 - direction * probe_step)
        if abs(x_probe - old_28) < 1e-9:
            return old_28, old_gap, 0

    x_probe_val, g_probe = evaluate(x_probe)
    eval_count += 1

    if abs(g_probe) <= gap_tolerance:
        return x_probe_val, g_probe, eval_count

    slope = (g_probe - old_gap) / (x_probe_val - old_28)
    if abs(slope) < 1e-9:
        # Flat — can't solve.
        candidates = [(old_28, old_gap), (x_probe_val, g_probe)]
        best = min(candidates, key=lambda p: abs(p[1]))
        return best[0], best[1], eval_count

    # Newton step to gap=0
    x_newton = clamp(old_28 - old_gap / slope)
    if abs(x_newton - x_probe_val) < 1e-9 and abs(x_newton - old_28) < 1e-9:
        # Same as probe or current — no new info
        candidates = [(old_28, old_gap), (x_probe_val, g_probe)]
        best = min(candidates, key=lambda p: abs(p[1]))
        return best[0], best[1], eval_count

    x_newton_val, g_newton = evaluate(x_newton)
    eval_count += 1

    if abs(g_newton) <= gap_tolerance:
        return x_newton_val, g_newton, eval_count

    # One correction via secant between the two latest points
    if abs(g_newton - g_probe) > 1e-9 and abs(x_newton_val - x_probe_val) > 1e-9:
        correction = clamp(
            x_newton_val - g_newton * (x_newton_val - x_probe_val) / (g_newton - g_probe)
        )
        # Bound the correction jump for safety
        correction = max(
            x_newton_val - max_correction_jump,
            min(x_newton_val + max_correction_jump, correction),
        )
        if abs(correction - x_newton_val) > 1e-9:
            corr_val, g_corr = evaluate(correction)
            eval_count += 1
            candidates = [
                (old_28, old_gap),
                (x_probe_val, g_probe),
                (x_newton_val, g_newton),
                (corr_val, g_corr),
            ]
            best = min(candidates, key=lambda p: abs(p[1]))
            return best[0], best[1], eval_count

    # Pick best of the three probes
    candidates = [(old_28, old_gap), (x_probe_val, g_probe), (x_newton_val, g_newton)]
    best = min(candidates, key=lambda p: abs(p[1]))
    return best[0], best[1], eval_count
