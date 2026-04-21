"""Idempotency short-circuit for expensive recalc functions.

The two big recalc functions (recalc_all_renewables_full, recalc_all_verbrauch)
are pure functions of their inputs — given the same input state they produce
the same output. Inside a balance settle loop they get called up to ~29 times,
but only 1-3 of those calls actually change anything. The rest are pure waste.

This module computes a lightweight signature of the relevant INPUT rows at
function entry, compares it to the signature stored from the previous call,
and returns the cached result if unchanged. Signature is computed via 4 small
SELECTs — far cheaper than the ~1761 queries a full recalc pass fires.

The signature intentionally EXCLUDES rows that the recalc itself writes to
(e.g. is_fixed=False Renewables for recalc_all_renewables_full). Otherwise
the signature would differ from pre-call to post-call and the cache would
never hit.

Cache is process-local. Each gunicorn worker has its own. That's fine:
worst case is "one real recalc per worker per input change", which is what
we want. No cross-process invalidation needed.
"""
from typing import Any, Callable, Tuple

_cache: dict[str, tuple[int, Any]] = {}


def _hash_tuple_of_rows(qs_values) -> int:
    """Hash a queryset.values_list(...) result into a stable integer."""
    return hash(tuple(qs_values))


def renewables_inputs_signature() -> int:
    """Signature for recalc_all_renewables_full inputs.

    Inputs: LandUse, all VerbrauchData (ziel+status+user_percent), fixed
    Renewables, renewable Formulas.
    Excludes: non-fixed Renewables (those are written by the recalc).

    user_percent is included because it's the user-editable input field
    even on rows where ziel is a calculated output. When the user edits
    user_percent and the verbrauch recalc runs, renewable outputs must
    reflect the new ziel values propagated from user_percent.
    """
    from simulator.models import LandUse, VerbrauchData, RenewableData, Formula
    from simulator.models import FormulaVariable

    lu = tuple(LandUse.objects.order_by('code').values_list(
        'code', 'target_ha', 'status_ha', 'user_percent'
    ))
    v = tuple(VerbrauchData.objects.order_by('code').values_list(
        'code', 'ziel', 'status', 'user_percent'
    ))
    rf = tuple(RenewableData.objects.filter(is_fixed=True).order_by('code').values_list(
        'code', 'target_value', 'status_value'
    ))
    f = tuple(Formula.objects.filter(category='renewable', is_active=True).order_by('key').values_list(
        'key', 'expression'
    ))
    fv = tuple(FormulaVariable.objects.filter(
        formula__category='renewable', formula__is_active=True
    ).order_by('formula_id', 'variable_name').values_list(
        'formula_id', 'variable_name', 'source_type', 'source_key'
    ))
    return hash((lu, v, rf, f, fv))


def verbrauch_inputs_signature() -> int:
    """Signature for recalc_all_verbrauch inputs.

    CRITICAL: user_percent is the user's editable input even on rows where
    ziel is computed. Previously this signature filtered to rows with
    is_calculated=False AND ziel_calculated=False — which excluded exactly
    the rows users edit via the UI. The cache then never invalidated on user
    edits, making "Save and Continue" a silent no-op.

    Fix: include user_percent of ALL rows (it's never written by the recalc,
    only by user saves), PLUS ziel/status of non-calculated rows as before.
    """
    from simulator.models import LandUse, VerbrauchData, RenewableData, Formula
    from simulator.models import FormulaVariable

    lu = tuple(LandUse.objects.order_by('code').values_list(
        'code', 'target_ha', 'status_ha', 'user_percent'
    ))
    # user_percent of all rows — user's knob, never written by the recalc.
    all_user_percents = tuple(
        VerbrauchData.objects.order_by('code').values_list('code', 'user_percent')
    )
    # Stored ziel/status of input rows (rows the recalc does NOT rewrite).
    v_inputs = tuple(VerbrauchData.objects.filter(
        is_calculated=False,
        status_calculated=False,
        ziel_calculated=False,
    ).order_by('code').values_list(
        'code', 'ziel', 'status'
    ))
    r = tuple(RenewableData.objects.order_by('code').values_list(
        'code', 'target_value', 'status_value'
    ))
    f = tuple(Formula.objects.filter(category='verbrauch', is_active=True).order_by('key').values_list(
        'key', 'expression'
    ))
    fv = tuple(FormulaVariable.objects.filter(
        formula__category='verbrauch', formula__is_active=True
    ).order_by('formula_id', 'variable_name').values_list(
        'formula_id', 'variable_name', 'source_type', 'source_key'
    ))
    return hash((lu, all_user_percents, v_inputs, r, f, fv))


def check_and_run(
    cache_key: str,
    signature_fn: Callable[[], int],
    run_fn: Callable[[], Any],
    empty_result_on_hit: Any = None,
) -> Any:
    """Short-circuit wrapper. Compute signature; if unchanged since last run,
    return `empty_result_on_hit` (NOT the original cached result).

    Why not the cached result: callers like `_run_verbrauch_recalc_passes`
    loop while `len(updated_codes) > 0`. If a cache hit returned the prior
    non-empty list, the outer loop would never break. Returning an empty-
    shaped value tells callers "nothing to update this time" which is
    exactly what a cache hit means.

    Callers that want the full result (not just the "did anything change?"
    signal) should bypass this wrapper."""
    sig = signature_fn()
    cached = _cache.get(cache_key)
    if cached is not None and cached[0] == sig:
        return empty_result_on_hit
    result = run_fn()
    _cache[cache_key] = (sig, result)
    return result


def invalidate(cache_key: str | None = None) -> None:
    """Clear cache. Exposed for tests and for explicit invalidation paths."""
    if cache_key is None:
        _cache.clear()
    else:
        _cache.pop(cache_key, None)
