from contextlib import contextmanager
from threading import local

from django.db import models

_state = local()

def _normalize_owner_id(user_or_id):
    if user_or_id is None:
        return None
    if isinstance(user_or_id, int):
        return user_or_id
    return getattr(user_or_id, "id", None)

def set_current_owner(user_or_id):
    _state.owner_id = _normalize_owner_id(user_or_id)
    _state.owner_presence_cache = {}

def reset_current_owner():
    _state.owner_id = None
    _state.owner_presence_cache = {}

def get_current_owner_id():
    return getattr(_state, "owner_id", None)

@contextmanager
def owner_scope(user_or_id):
    prev_owner = get_current_owner_id()
    prev_cache = getattr(_state, "owner_presence_cache", {})
    set_current_owner(user_or_id)
    try:
        yield
    finally:
        _state.owner_id = prev_owner
        _state.owner_presence_cache = prev_cache

class OwnerScopedManager(models.Manager):
    """
    Default manager for user-isolated simulation data.
    - If an owner context exists and owner rows exist -> return only owner rows
    - If owner context exists but owner rows missing -> fallback to global rows (owner is null)
    - If no owner context -> return global rows (owner is null)
    """

    def get_queryset(self):
        qs = super().get_queryset()

        if not any(f.name == "owner" for f in self.model._meta.concrete_fields):
            return qs

        owner_id = get_current_owner_id()
        if owner_id is None:
            return qs.filter(owner__isnull=True)

        cache = getattr(_state, "owner_presence_cache", {})
        cache_key = self.model._meta.label_lower
        has_owner_rows = cache.get(cache_key)
        if has_owner_rows is None:
            has_owner_rows = qs.filter(owner_id=owner_id).exists()
            cache[cache_key] = has_owner_rows
            _state.owner_presence_cache = cache

        if has_owner_rows:
            return qs.filter(owner_id=owner_id)

        return qs.filter(owner__isnull=True)
