from django.db import transaction


def _template_sync_fields(model, exclude_fields=None):
    exclude = set(exclude_fields or [])
    return [
        f.name
        for f in model._meta.concrete_fields
        if f.name not in {"id", "owner", "region", "created_at", "updated_at"}
        and f.name not in exclude
    ]


def _clone_simple_model(model, user, region, exclude_fields=None):
    exclude = set(exclude_fields or [])
    fields = _template_sync_fields(model, exclude)

    source_rows = list(
        model.all_objects.filter(owner__isnull=True, region=region).order_by("id")
    )
    if not source_rows:
        return 0

    clones = []
    for row in source_rows:
        data = {name: getattr(row, name) for name in fields}
        data["owner"] = user
        data["region"] = region
        clones.append(model(**data))

    model.all_objects.bulk_create(clones, batch_size=1000)
    return len(clones)


def _sync_simple_template_to_user_rows(template_row, exclude_fields=None):
    if getattr(template_row, "owner_id", None) is not None:
        return 0

    model = type(template_row)
    lookup_field = "tag_im_jahr" if model.__name__ == "WSData" else "code"
    lookup_value = getattr(template_row, lookup_field, None)
    if lookup_value in (None, ""):
        return 0

    fields = _template_sync_fields(model, exclude_fields)
    updates = {name: getattr(template_row, name) for name in fields}

    return model.all_objects.filter(
        owner__isnull=False,
        region=template_row.region,
        **{lookup_field: lookup_value},
    ).update(**updates)


def _clone_landuse_for_user(LandUse, user, region):
    source_rows = list(
        LandUse.all_objects.filter(owner__isnull=True, region=region).order_by("id")
    )
    if not source_rows:
        return 0

    clones = []
    for row in source_rows:
        clones.append(
            LandUse(
                owner=user,
                region=region,
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
                # §2.3 Phase A provenance — carry from base so popover renders
                # immediately when a fresh user gets a workspace.
                source_url=row.source_url,
                notes_assumption=row.notes_assumption,
                source_refs=row.source_refs,
                origin=row.origin,
            )
        )

    LandUse.all_objects.bulk_create(clones, batch_size=1000)

    created_rows = list(
        LandUse.all_objects.filter(owner=user, region=region).order_by("id")
    )
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


def sync_landuse_template_to_user_rows(template_row):
    """
    Keep existing user workspaces aligned when a shared admin LandUse row is
    edited. The web UI reads user rows first, so without this sync an admin
    change can look correct in admin but stale in the webapp.
    """
    if getattr(template_row, "owner_id", None) is not None:
        return 0

    updated = _sync_simple_template_to_user_rows(template_row, exclude_fields={"parent"})

    if template_row.parent_id:
        user_rows = type(template_row).all_objects.filter(
            owner__isnull=False,
            region=template_row.region,
            code=template_row.code,
        )
        for row in user_rows:
            parent = type(template_row).all_objects.filter(
                owner_id=row.owner_id,
                region=template_row.region,
                code=template_row.parent.code,
            ).first()
            if parent and row.parent_id != parent.id:
                type(template_row).all_objects.filter(pk=row.pk).update(parent=parent)

    return updated


def sync_template_to_user_rows(template_row):
    if template_row.__class__.__name__ == "LandUse":
        return sync_landuse_template_to_user_rows(template_row)
    return _sync_simple_template_to_user_rows(template_row)


def sync_all_templates_to_user_rows(region_code=None):
    """
    One-time repair helper for already-existing databases. It copies current
    shared admin/template values into all existing user workspace copies.
    """
    from simulator.models import LandUse, Region, RenewableData, VerbrauchData
    from simulator.ws_models import WSData

    regions = Region.objects.all()
    if region_code:
        regions = regions.filter(code=region_code)

    updated = 0
    for region in regions:
        for model in (LandUse, RenewableData, VerbrauchData, WSData):
            for row in model.all_objects.filter(owner__isnull=True, region=region):
                updated += sync_template_to_user_rows(row)
    return updated


def ensure_user_workspace_data(user, region_code="DE"):
    """
    Ensure a logged-in webapp user has isolated simulation data rows for the
    given region. Copies current global baseline rows on first use.

    Phase B (T65): per-(owner, region) scoping. If `region_code` is
    omitted, defaults to DE so existing single-region call sites keep
    working unchanged.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return

    from simulator.models import LandUse, RenewableData, Region, VerbrauchData
    from simulator.ws_models import WSData

    try:
        region = Region.objects.get(code=region_code)
    except Region.DoesNotExist:
        # Unknown region (typo, future Bundesland not yet seeded) — bail
        # silently rather than 500 the request. Active region falls back
        # to DE on the next click of the region switcher.
        return

    with transaction.atomic():
        if not LandUse.all_objects.filter(owner=user, region=region).exists():
            _clone_landuse_for_user(LandUse, user, region)

        if not RenewableData.all_objects.filter(owner=user, region=region).exists():
            _clone_simple_model(RenewableData, user, region)

        if not VerbrauchData.all_objects.filter(owner=user, region=region).exists():
            _clone_simple_model(VerbrauchData, user, region)

        # Phase C (T66): WSData is now per-(owner, region) — same shape
        # as the parameter models. Switching active region surfaces a
        # different 365-day overlay; first-use clones the active region's
        # base WSData rows.
        if not WSData.all_objects.filter(owner=user, region=region).exists():
            _clone_simple_model(WSData, user, region)


# Phase C (T66): _clone_simple_model_no_region removed — every model
# the workspace clones now carries a region FK. Region-aware
# _clone_simple_model above handles all of them uniformly.
