from __future__ import annotations

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
    """Signature over EVERYTHING that could affect renewable recalc output.

    Includes both inputs (LandUse, all VerbrauchData, fixed Renewables,
    Formulas) AND computed outputs (non-fixed RenewableData values).

    Including outputs is intentional: outer multi-pass loops (e.g.
    _run_verbrauch_recalc_passes) rely on fresh recalcs detecting further
    propagation after each pass's bulk_update. If the signature excluded
    outputs, pass N+1 would cache-hit on the same input signature and
    return empty, stopping convergence prematurely.

    True "inputs unchanged" cases (settle loops that don't touch anything)
    still hit the cache because all row values stay stable.
    """
    from simulator.models import LandUse, VerbrauchData, RenewableData, Formula
    from simulator.models import FormulaVariable

    lu = tuple(LandUse.objects.order_by('code').values_list(
        'code', 'target_ha', 'status_ha', 'user_percent'
    ))
    v = tuple(VerbrauchData.objects.order_by('code').values_list(
        'code', 'ziel', 'status', 'user_percent'
    ))
    # All renewables including computed ones — see docstring.
    r = tuple(RenewableData.objects.order_by('code').values_list(
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
    return hash((lu, v, r, f, fv))


def verbrauch_inputs_signature() -> int:
    """Signature over EVERYTHING that could affect verbrauch recalc output.

    See the note on renewables_inputs_signature: outputs are included so that
    multi-pass outer loops get fresh recalcs after each pass's bulk_update.
    """
    from simulator.models import LandUse, VerbrauchData, RenewableData, Formula
    from simulator.models import FormulaVariable

    lu = tuple(LandUse.objects.order_by('code').values_list(
        'code', 'target_ha', 'status_ha', 'user_percent'
    ))
    # All verbrauch rows including computed ones.
    v = tuple(VerbrauchData.objects.order_by('code').values_list(
        'code', 'ziel', 'status', 'user_percent'
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
    return hash((lu, v, r, f, fv))


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
