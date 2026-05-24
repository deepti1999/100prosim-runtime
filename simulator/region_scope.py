"""
Phase B (T65, SR-004) — thread-local active region scope.

Mirror of `simulator.owner_scope`. The middleware sets the active region
code per request (from session, default DE); querysets read it via
OwnerScopedManager to filter parameter rows to the active region.

Setting code=None (or calling reset_current_region) means "no region
filter" — preserves back-compat for callers that pre-date Phase B
(migrations, management commands without --region, etc.).
"""
from contextlib import contextmanager
from threading import local

_state = local()


def set_current_region(code):
    """Bind a region code (e.g. 'DE') to this thread."""
    _state.region_code = code


def reset_current_region():
    """Clear the bound region; queries fall back to no-region-filter."""
    _state.region_code = None


def get_current_region_code():
    """Return the bound region code or None if unset."""
    return getattr(_state, "region_code", None)


@contextmanager
def region_scope(code):
    """Temporarily bind `code` as the active region; restore on exit."""
    prev = get_current_region_code()
    set_current_region(code)
    try:
        yield
    finally:
        if prev is None:
            reset_current_region()
        else:
            set_current_region(prev)
