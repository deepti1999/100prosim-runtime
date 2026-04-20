from django.db import transaction

def _clone_simple_model(model, user, exclude_fields=None):
    exclude = set(exclude_fields or [])
    fields = [
        f.name
        for f in model._meta.concrete_fields
        if f.name not in {"id", "owner"} and f.name not in exclude
    ]

    source_rows = list(model.all_objects.filter(owner__isnull=True).order_by("id"))
    if not source_rows:
        return 0

    clones = []
    for row in source_rows:
        data = {name: getattr(row, name) for name in fields}
        data["owner"] = user
        clones.append(model(**data))

    model.all_objects.bulk_create(clones, batch_size=1000)
    return len(clones)

def _clone_landuse_for_user(LandUse, user):
    source_rows = list(LandUse.all_objects.filter(owner__isnull=True).order_by("id"))
    if not source_rows:
        return 0

    clones = []
    for row in source_rows:
        clones.append(
            LandUse(
                owner=user,
                code=row.code,
                name=row.name,
                status_ha=row.status_ha,
                target_ha=row.target_ha,
                status_formula_key=row.status_formula_key,
                target_formula_key=row.target_formula_key,
                user_percent=row.user_percent,
                increase_limit_baseline_percent=row.increase_limit_baseline_percent,
                target_locked=row.target_locked,
                parent=None,
                quelle=row.quelle,
            )
        )

    LandUse.all_objects.bulk_create(clones, batch_size=1000)

    created_rows = list(LandUse.all_objects.filter(owner=user).order_by("id"))
    created_by_code = {row.code: row for row in created_rows}
    source_by_code = {row.code: row for row in source_rows}

    updates = []
    for code, clone in created_by_code.items():
        source = source_by_code.get(code)
        if source and source.parent_id:
            source_parent = source.parent
            if source_parent is None:
                continue
            parent_clone = created_by_code.get(source_parent.code)
            if parent_clone and clone.parent_id != parent_clone.id:
                clone.parent_id = parent_clone.id
                updates.append(clone)

    if updates:
        LandUse.all_objects.bulk_update(updates, ["parent"])

    return len(clones)

def ensure_user_workspace_data(user):
    """
    Ensure a non-staff user has isolated simulation data rows.
    Copies current global baseline rows on first use.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return
    if getattr(user, "is_staff", False):
        return

    from simulator.models import LandUse, RenewableData, VerbrauchData
    from simulator.ws_models import WSData

    with transaction.atomic():
        if not LandUse.all_objects.filter(owner=user).exists():
            _clone_landuse_for_user(LandUse, user)

        if not RenewableData.all_objects.filter(owner=user).exists():
            _clone_simple_model(RenewableData, user)

        if not VerbrauchData.all_objects.filter(owner=user).exists():
            _clone_simple_model(VerbrauchData, user)

        if not WSData.all_objects.filter(owner=user).exists():
            _clone_simple_model(WSData, user)
