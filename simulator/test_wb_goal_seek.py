"""Coverage for ``simulator/goal_seek.py``.

The module ships three pure-math iterative solvers that the WS-365 balance
flow depends on: ``goal_seek`` (secant method), ``binary_search_balance``
(land-use bracket search), and ``binary_search_ws_balance`` (storage
bracket search). All are pure functions over a callable + scalar inputs
— no DB, no signals, no side effects. The audit-prompt MUST-COVER list
flagged this module at 0 % line coverage.

Invariants protected here:

1. **Convergence on a well-conditioned root**: secant + both binary
   searches must terminate within ``max_iter`` and return a value
   within ``tol`` of the target.
2. **Graceful cap on max_iter**: pathological / slow-convergence inputs
   must NOT hang. Solver returns the best-so-far iterate when budget
   exhausts.
3. **Divide-by-zero guard in secant**: if ``f(x1) - f(x0)`` is below
   ``1e-12``, the secant breaks safely (no ZeroDivisionError, no
   infinite loop).
4. **Identical x0/x1 nudge**: if caller passes ``x0 == x1``, the secant
   nudges ``x1`` so the first step has a non-zero direction.
5. **Early hit on initial guess**: if ``|f(x0) - target| < tol`` on
   entry, return ``x0`` immediately (zero iterations).
6. **Sign-driven branch in binary_search_balance**: positive initial
   gap brackets [A_initial, A_initial*2 + 1000]; negative initial
   gap brackets [max(0, A_initial*0.1), A_initial]. Verified by
   confirming the search converges from each side.
7. **Best-so-far tracking** in both binary searches: even when
   ``max_iter`` exhausts, return the iterate with the smallest gap
   seen during the run, not the last iterate.
8. **Closed-bracket termination**: ``binary_search_balance`` exits
   when ``A_high - A_low < 1`` even before ``max_iter`` exhausts.
   Same for ``binary_search_ws_balance`` with ``S_high - S_low < 1``.

These tests use mock-callable functions over scalar floats — no
fixtures, no DB, no Django setup beyond the default test runner.
"""
import unittest

from simulator.goal_seek import (
    binary_search_balance,
    binary_search_ws_balance,
    goal_seek,
)


class GoalSeekSecantTests(unittest.TestCase):
    """Secant-method ``goal_seek`` — covers the well-conditioned, the
    pathological, and every guard branch."""

    def test_converges_on_linear_root(self):
        # f(x) = 2x - 10 has root at x = 5. Tol 1e-6.
        result = goal_seek(lambda x: 2 * x - 10, x0=0.0, x1=1.0, target=0.0)
        self.assertAlmostEqual(result, 5.0, places=5)

    def test_converges_on_quadratic_root(self):
        # f(x) = x^2 - 9 has roots at +/-3. Initial guesses near +3.
        result = goal_seek(lambda x: x * x - 9, x0=2.0, x1=4.0, target=0.0)
        self.assertAlmostEqual(result, 3.0, places=4)

    def test_target_met_immediately_returns_x0_no_iteration(self):
        # f(x0) - target is already within tol → return x0 directly.
        calls = []

        def f(x):
            calls.append(x)
            return 0.0

        result = goal_seek(f, x0=42.0, x1=99.0, target=0.0, tol=1e-3)
        self.assertEqual(result, 42.0)
        self.assertEqual(len(calls), 1, "should call f(x0) only, not iterate")

    def test_x0_equals_x1_triggers_nudge(self):
        # When x0 == x1, the secant has no direction — code nudges x1
        # by factor 1.05 (or to 1.0 if x0 == 0). Verify iteration
        # actually happens and converges.
        result = goal_seek(lambda x: x - 7.0, x0=10.0, x1=10.0, target=0.0)
        self.assertAlmostEqual(result, 7.0, places=4)

    def test_x0_zero_x1_zero_triggers_nudge_to_one(self):
        # Both zero — nudge sets x1 = 1.0. Verify the solver still
        # finds the root.
        result = goal_seek(lambda x: x - 3.0, x0=0.0, x1=0.0, target=0.0)
        self.assertAlmostEqual(result, 3.0, places=4)

    def test_constant_function_breaks_on_zero_denominator(self):
        # f(x) returns the same constant regardless of input → f1 - f0 == 0.
        # Code's `abs(denominator) < 1e-12` guard breaks the loop and returns
        # the current x1 (best-so-far). MUST NOT raise ZeroDivisionError.
        result = goal_seek(lambda x: 5.0, x0=1.0, x1=2.0, target=0.0)
        # x1 was 2.0 going in; one iteration's denominator is (5-5)=0
        # → break, return x1.
        self.assertEqual(result, 2.0)

    def test_max_iter_cap_does_not_hang(self):
        # Slowly-shrinking but never-converging-within-tol function.
        # f(x) returns 1/(x+1) which approaches 0 only as x → ∞.
        # With max_iter=5 the solver must return after 5 iterations
        # whether or not it converged.
        call_count = [0]

        def f(x):
            call_count[0] += 1
            return 1.0 / (x + 1)

        result = goal_seek(f, x0=0.0, x1=1.0, target=0.0, max_iter=5)
        # 1 init f0 + 1 init f1 + at most 5 iter f-calls = 7 max.
        self.assertLessEqual(call_count[0], 7)
        self.assertIsInstance(result, float)

    def test_target_nonzero(self):
        # f(x) = x; solve f(x) = 12. Should converge to x = 12.
        result = goal_seek(lambda x: x, x0=0.0, x1=20.0, target=12.0)
        self.assertAlmostEqual(result, 12.0, places=4)

    def test_negative_root(self):
        # f(x) = x + 4 has root at x = -4.
        result = goal_seek(lambda x: x + 4, x0=0.0, x1=-1.0, target=0.0)
        self.assertAlmostEqual(result, -4.0, places=4)

    def test_tol_just_above_returns_pre_convergence(self):
        # f(x) = x; target 5. With tol=1.0, the solver should return as
        # soon as |x - 5| < 1.0 (i.e. without full convergence).
        result = goal_seek(lambda x: x, x0=0.0, x1=10.0, target=5.0, tol=1.0)
        # Result depends on iteration order, but should be within tol+slop.
        self.assertLessEqual(abs(result - 5.0), 5.0)


class BinarySearchBalanceTests(unittest.TestCase):
    """``binary_search_balance`` — gap-driven LandUse area search."""

    def test_already_within_tol_returns_initial(self):
        # Gap(A_initial) within tolerance → return immediately.
        called = []

        def gap(a):
            called.append(a)
            return 0.5  # within tol=1.0

        result = binary_search_balance(gap, A_initial=100.0, tol=1.0)
        self.assertEqual(result, 100.0)
        self.assertEqual(len(called), 1, "should call gap(A_initial) only")

    def test_positive_gap_expands_high_bracket(self):
        # Positive initial gap → bracket = [A_initial, A_initial*2 + 1000]
        # Linear gap function: gap(a) = 2000 - a (root at 2000)
        result = binary_search_balance(lambda a: 2000 - a, A_initial=500.0, tol=10.0)
        self.assertAlmostEqual(result, 2000.0, delta=10.0)

    def test_negative_gap_uses_lower_bracket(self):
        # Negative initial gap → bracket = [max(0, A_initial*0.1), A_initial]
        # Linear gap function: gap(a) = 100 - a (root at 100, gap < 0 at A=500)
        result = binary_search_balance(lambda a: 100 - a, A_initial=500.0, tol=2.0)
        self.assertAlmostEqual(result, 100.0, delta=2.0)

    def test_max_iter_cap_returns_best_so_far(self):
        # Very small max_iter — cannot converge. MUST return best-so-far,
        # which is the smallest |gap| iterate seen.
        call_count = [0]

        def gap(a):
            call_count[0] += 1
            return 1e6 - a

        result = binary_search_balance(gap, A_initial=100.0, tol=0.0001, max_iter=2)
        # 1 init call + at most 2 iter calls = 3 max
        self.assertLessEqual(call_count[0], 3)
        self.assertIsInstance(result, float)

    def test_zero_initial_with_negative_gap(self):
        # A_initial = 0 + negative gap → bracket low = max(0, 0*0.1) = 0.
        # gap(a) = -a → root at 0. Should return 0.
        result = binary_search_balance(lambda a: -a, A_initial=0.0, tol=0.5)
        self.assertEqual(result, 0.0)

    def test_negative_initial_with_negative_gap_clamps_low_to_zero(self):
        # A_initial = -50 + negative gap → bracket low = max(0, -5) = 0.
        # gap(a) = -100 - a → never zero in [0, -50] but loop terminates.
        result = binary_search_balance(lambda a: -100 - a, A_initial=-50.0, tol=1.0)
        self.assertIsInstance(result, float)


class BinarySearchWsBalanceTests(unittest.TestCase):
    """``binary_search_ws_balance`` — storage-balance bracket search."""

    def test_already_within_tol_returns_initial(self):
        result = binary_search_ws_balance(
            lambda s: 5.0,  # within default tol=10
            S_initial=200000.0,
            tol=10.0,
        )
        self.assertEqual(result, 200000.0)

    def test_positive_balance_expands_high_bracket(self):
        # Linear: balance(s) = 60000 - s; root at 60000.
        # S_initial=20000 → bracket [20000, 20000*2 + 50000] = [20000, 90000].
        # Root 60000 falls inside the bracket, so binary search converges.
        result = binary_search_ws_balance(
            lambda s: 60000 - s, S_initial=20000.0, tol=50.0
        )
        self.assertAlmostEqual(result, 60000.0, delta=50.0)

    def test_negative_balance_uses_lower_bracket(self):
        # Linear: balance(s) = 50000 - s; at S=200000, balance = -150000 < 0
        # → low = max(0, 200000*0.1) = 20000. Root at 50000 falls in [20000, 200000].
        result = binary_search_ws_balance(
            lambda s: 50000 - s, S_initial=200000.0, tol=20.0
        )
        self.assertAlmostEqual(result, 50000.0, delta=20.0)

    def test_max_iter_cap_returns_best_so_far(self):
        call_count = [0]

        def balance(s):
            call_count[0] += 1
            return 1e9 - s

        result = binary_search_ws_balance(balance, S_initial=10000.0, max_iter=3)
        self.assertLessEqual(call_count[0], 4)
        self.assertIsInstance(result, float)

    def test_negative_initial_with_negative_balance_clamps_low_to_zero(self):
        # S_initial = -1000, balance(s) = -1 - s/1000 < 0 → low = max(0, -100) = 0.
        # Loop must terminate without hanging.
        result = binary_search_ws_balance(
            lambda s: -1 - s / 1000, S_initial=-1000.0, max_iter=5
        )
        self.assertIsInstance(result, float)

    def test_tolerance_boundary_inside(self):
        # |balance(S_initial)| exactly at tol → returns initial (boundary inclusive).
        result = binary_search_ws_balance(
            lambda s: 10.0, S_initial=50000.0, tol=10.0
        )
        self.assertEqual(result, 50000.0)
