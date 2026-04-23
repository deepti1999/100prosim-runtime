import json

from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import BaselineSnapshot, LandUse, RenewableData, ScenarioSnapshot, VerbrauchData
from .ws_models import WSData

MAX_SCENARIOS_PER_SCOPE = 30
ACTIVE_SCENARIO_SCOPE_KEY = "active_scenario_scope"
ACTIVE_SCENARIO_ID_KEY = "active_scenario_id"
ACTIVE_SCENARIO_NAME_KEY = "active_scenario_name"
ACTIVE_SCENARIO_UPDATED_AT_KEY = "active_scenario_updated_at"

def _baseline_scope(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_staff:
        return {"key": "global", "owner": None, "label": "global"}
    if user and user.is_authenticated:
        return {"key": f"user:{user.id}", "owner": user, "label": "workspace"}
    return {"key": "global", "owner": None, "label": "global"}

def _scope_filter(owner):
    return {"owner__isnull": True} if owner is None else {"owner": owner}

def _set_active_scenario_session(request, scope_key, scenario):
    request.session[ACTIVE_SCENARIO_SCOPE_KEY] = scope_key
    request.session[ACTIVE_SCENARIO_ID_KEY] = scenario.id
    request.session[ACTIVE_SCENARIO_NAME_KEY] = scenario.name
    request.session[ACTIVE_SCENARIO_UPDATED_AT_KEY] = timezone.localtime(scenario.updated_at).strftime("%d.%m.%Y %H:%M")
    request.session.modified = True

def _clear_active_scenario_session(request, scope_key=None):
    current_scope = request.session.get(ACTIVE_SCENARIO_SCOPE_KEY)
    if scope_key is not None and current_scope != scope_key:
        return
    request.session.pop(ACTIVE_SCENARIO_SCOPE_KEY, None)
    request.session.pop(ACTIVE_SCENARIO_ID_KEY, None)
    request.session.pop(ACTIVE_SCENARIO_NAME_KEY, None)
    request.session.pop(ACTIVE_SCENARIO_UPDATED_AT_KEY, None)
    request.session.modified = True

def _serialize_model_rows(model, owner, exclude_fields=None):
    exclude = set(exclude_fields or [])
    field_names = [
        f.name
        for f in model._meta.concrete_fields
        # Phase B (T65): skip `region` here — the FK serializes to a Region
        # object which isn't JSON-serializable. On restore, the model's
        # default callable assigns DE; per-region snapshots arrive with
        # the Bundesländer phase via a top-level region_code key instead.
        if f.name not in {"id", "owner", "region", "created_at", "updated_at"} and f.name not in exclude
    ]
    rows = model.all_objects.filter(**_scope_filter(owner)).order_by("id")
    serialized = []
    for row in rows:
        serialized.append({name: getattr(row, name) for name in field_names})
    return serialized

def _serialize_landuse_rows(owner):
    rows = LandUse.all_objects.filter(**_scope_filter(owner)).order_by("id")
    serialized = []
    for row in rows:
        serialized.append({
            "code": row.code,
            "name": row.name,
            "status_ha": row.status_ha,
            "target_ha": row.target_ha,
            "status_formula_key": row.status_formula_key,
            "target_formula_key": row.target_formula_key,
            "user_percent": row.user_percent,
            "increase_limit_baseline_percent": row.increase_limit_baseline_percent,
            "target_locked": row.target_locked,
            "quelle": row.quelle,
            "parent_code": row.parent.code if row.parent else None,
        })
    return serialized

def _restore_model_rows(model, owner, rows):
    existing_qs = model.all_objects.filter(**_scope_filter(owner))
    if existing_qs.exists():
        existing_qs._raw_delete(existing_qs.db)
    if not rows:
        return 0

    allowed_fields = {
        f.name for f in model._meta.concrete_fields
        # Phase B (T65): match the serialize-side exclusion of `region`;
        # restored rows get DE via the model's default callable.
        if f.name not in {"id", "owner", "region", "created_at", "updated_at"}
    }
    to_create = []
    for row in rows:
        payload = {k: v for k, v in row.items() if k in allowed_fields}
        payload["owner"] = owner
        to_create.append(model(**payload))
    model.all_objects.bulk_create(to_create, batch_size=1000)
    return len(to_create)

def _restore_landuse_rows(owner, rows):
    existing_qs = LandUse.all_objects.filter(**_scope_filter(owner))
    if existing_qs.exists():
        existing_qs._raw_delete(existing_qs.db)
    if not rows:
        return 0

    create_objs = []
    for row in rows:
        create_objs.append(
            LandUse(
                owner=owner,
                code=row.get("code"),
                name=row.get("name"),
                status_ha=row.get("status_ha"),
                target_ha=row.get("target_ha"),
                status_formula_key=row.get("status_formula_key"),
                target_formula_key=row.get("target_formula_key"),
                user_percent=row.get("user_percent"),
                increase_limit_baseline_percent=row.get("increase_limit_baseline_percent"),
                target_locked=bool(row.get("target_locked")),
                quelle=row.get("quelle"),
                parent=None,
            )
        )
    LandUse.all_objects.bulk_create(create_objs, batch_size=1000)

    created = list(LandUse.all_objects.filter(**_scope_filter(owner)).order_by("id"))
    by_code = {item.code: item for item in created}
    updates = []
    for row in rows:
        code = row.get("code")
        parent_code = row.get("parent_code")
        if not code or not parent_code:
            continue
        child = by_code.get(code)
        parent = by_code.get(parent_code)
        if child and parent and child.parent_id != parent.id:
            child.parent_id = parent.id
            updates.append(child)
    if updates:
        LandUse.all_objects.bulk_update(updates, ["parent"])
    return len(create_objs)

def _snapshot_size_mb(payload):
    size_bytes = len(json.dumps(payload, default=str).encode("utf-8"))
    return round(size_bytes / (1024 * 1024), 2)

def _snapshot_payload_for_owner(owner):
    return {
        "landuse": _serialize_landuse_rows(owner),
        "renewable": _serialize_model_rows(RenewableData, owner),
        "verbrauch": _serialize_model_rows(VerbrauchData, owner),
        "ws": _serialize_model_rows(WSData, owner),
    }

def _restore_snapshot_payload(owner, payload):
    payload = payload or {}
    with transaction.atomic():
        _restore_landuse_rows(owner, payload.get("landuse", []))
        _restore_model_rows(RenewableData, owner, payload.get("renewable", []))
        _restore_model_rows(VerbrauchData, owner, payload.get("verbrauch", []))
        _restore_model_rows(WSData, owner, payload.get("ws", []))

def _scenario_scope_filter(owner):
    return {"owner__isnull": True} if owner is None else {"owner": owner}

def _default_scenario_name():
    ts = timezone.localtime().strftime("%Y-%m-%d %H:%M")
    return f"Scenario {ts}"

# Stakeholder PDF §2.4.2 (T16, T17, T18): there is exactly one
# admin-provided baseline, stored with key="global" and owner=None.
# All users restore from that single snapshot. Regular users cannot
# create or overwrite it — only staff can.
ADMIN_BASELINE_KEY = "global"


def _admin_baseline_snapshot():
    """Return the single shared admin baseline snapshot (or None)."""
    return BaselineSnapshot.objects.filter(key=ADMIN_BASELINE_KEY).first()


@login_required
@csrf_exempt
def create_baseline(request):
    """Create / update the shared admin baseline. Staff only (T18)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    user = request.user
    if not user.is_staff:
        return JsonResponse({
            'status': 'error',
            'error': 'Nur Administratoren können die Baseline neu anlegen.',
        }, status=403)

    try:
        # The admin baseline captures the shared/global rows (owner=None),
        # matching the "global" scope admins edit. This is what every user
        # will see when they "Auf Baseline zurücksetzen".
        payload = _snapshot_payload_for_owner(None)

        BaselineSnapshot.objects.update_or_create(
            key=ADMIN_BASELINE_KEY,
            defaults={
                "owner": None,
                "payload": payload,
            },
        )
        snapshot = _admin_baseline_snapshot()

        return JsonResponse({
            'status': 'ok',
            'message': 'Baseline snapshot created successfully',
            'created_at': snapshot.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'size_mb': _snapshot_size_mb(payload),
            'scope': 'admin-baseline',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def restore_baseline(request):
    """Restore the shared admin baseline into THIS user's workspace (T17, T18)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    try:
        snapshot = _admin_baseline_snapshot()
        if snapshot is None:
            return JsonResponse({
                'status': 'error',
                'error': 'Noch keine Baseline vorhanden. Ein Administrator muss die Baseline einmalig anlegen.',
            }, status=404)

        # IMPORTANT: restore into the caller's workspace (per-user data),
        # using the admin baseline as the source-of-truth payload.
        user = request.user
        target_owner = None if (user.is_authenticated and user.is_staff) else user
        _restore_snapshot_payload(target_owner, snapshot.payload)

        scope = _baseline_scope(request)
        _clear_active_scenario_session(request, scope["key"])

        return JsonResponse({
            'status': 'ok',
            'message': 'Baseline restored successfully. Please refresh the page.',
            'scope': scope["label"],
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def get_baseline_info(request):
    """Info about the shared admin baseline (visible to all users)."""
    try:
        snapshot = _admin_baseline_snapshot()
        if snapshot is None:
            return JsonResponse({
                'status': 'ok',
                'exists': False,
                'scope': 'admin-baseline',
                'can_create': request.user.is_staff,
            })

        payload = snapshot.payload or {}
        return JsonResponse({
            'status': 'ok',
            'exists': True,
            'created_at': snapshot.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'size_mb': _snapshot_size_mb(payload),
            'scope': 'admin-baseline',
            'can_create': request.user.is_staff,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def create_scenario(request):
    """Create a named scenario snapshot for current scope."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    try:
        scope = _baseline_scope(request)
        owner = scope["owner"]
        data = json.loads(request.body or "{}")
        raw_name = str(data.get("name") or "").strip()
        note = str(data.get("note") or "").strip()
        name = raw_name or _default_scenario_name()

        scoped_qs = ScenarioSnapshot.objects.filter(**_scenario_scope_filter(owner))
        if scoped_qs.count() >= MAX_SCENARIOS_PER_SCOPE:
            return JsonResponse({
                'status': 'error',
                'error': f'Maximum {MAX_SCENARIOS_PER_SCOPE} scenarios reached. Delete one and try again.'
            }, status=400)

        if scoped_qs.filter(name__iexact=name).exists():
            return JsonResponse({
                'status': 'error',
                'error': 'Scenario name already exists in this scope. Choose a different name.'
            }, status=400)

        payload = _snapshot_payload_for_owner(owner)
        scenario = ScenarioSnapshot.objects.create(
            owner=owner,
            name=name,
            note=note,
            payload=payload,
        )
        _set_active_scenario_session(request, scope["key"], scenario)
        return JsonResponse({
            'status': 'ok',
            'id': scenario.id,
            'name': scenario.name,
            'note': scenario.note,
            'created_at': scenario.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'size_mb': _snapshot_size_mb(payload),
            'scope': scope["label"],
            'message': 'Scenario saved successfully.',
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
def list_scenarios(request):
    """List named scenarios for current scope."""
    try:
        scope = _baseline_scope(request)
        owner = scope["owner"]
        scenarios = (
            ScenarioSnapshot.objects
            .filter(**_scenario_scope_filter(owner))
            .order_by("-updated_at")
        )
        items = [
            {
                "id": s.id,
                "name": s.name,
                "note": s.note,
                "created_at": s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "size_mb": _snapshot_size_mb(s.payload or {}),
            }
            for s in scenarios
        ]
        return JsonResponse({
            "status": "ok",
            "scope": scope["label"],
            "items": items,
            "max_items": MAX_SCENARIOS_PER_SCOPE,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def restore_scenario(request, scenario_id):
    """Restore one named scenario for current scope."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    try:
        scope = _baseline_scope(request)
        owner = scope["owner"]
        scenario = ScenarioSnapshot.objects.filter(
            id=scenario_id,
            **_scenario_scope_filter(owner),
        ).first()
        if scenario is None:
            return JsonResponse({'status': 'error', 'error': 'Scenario not found.'}, status=404)

        _restore_snapshot_payload(owner, scenario.payload)
        _set_active_scenario_session(request, scope["key"], scenario)
        return JsonResponse({
            'status': 'ok',
            'message': f'Scenario "{scenario.name}" restored successfully. Please refresh the page.',
            'scope': scope["label"],
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def rename_scenario(request, scenario_id):
    """Rename a scenario in current scope."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    try:
        scope = _baseline_scope(request)
        owner = scope["owner"]
        data = json.loads(request.body or "{}")
        new_name = str(data.get("name") or "").strip()
        if not new_name:
            return JsonResponse({'status': 'error', 'error': 'New name is required.'}, status=400)

        scenario = ScenarioSnapshot.objects.filter(
            id=scenario_id,
            **_scenario_scope_filter(owner),
        ).first()
        if scenario is None:
            return JsonResponse({'status': 'error', 'error': 'Scenario not found.'}, status=404)

        duplicate = (
            ScenarioSnapshot.objects
            .filter(**_scenario_scope_filter(owner), name__iexact=new_name)
            .exclude(id=scenario.id)
            .exists()
        )
        if duplicate:
            return JsonResponse({'status': 'error', 'error': 'Scenario name already exists.'}, status=400)

        scenario.name = new_name
        scenario.save(update_fields=["name", "updated_at"])
        if request.session.get(ACTIVE_SCENARIO_ID_KEY) == scenario.id:
            _set_active_scenario_session(request, scope["key"], scenario)
        return JsonResponse({
            'status': 'ok',
            'message': 'Scenario renamed successfully.',
            'id': scenario.id,
            'name': scenario.name,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def delete_scenario(request, scenario_id):
    """Delete a scenario in current scope."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'POST required'}, status=405)

    try:
        scope = _baseline_scope(request)
        owner = scope["owner"]
        scenario = ScenarioSnapshot.objects.filter(
            id=scenario_id,
            **_scenario_scope_filter(owner),
        ).first()
        if scenario is None:
            return JsonResponse({'status': 'error', 'error': 'Scenario not found.'}, status=404)

        deleted_name = scenario.name
        was_active = request.session.get(ACTIVE_SCENARIO_ID_KEY) == scenario.id
        scenario.delete()
        if was_active:
            _clear_active_scenario_session(request, scope["key"])
        return JsonResponse({
            'status': 'ok',
            'message': f'Scenario "{deleted_name}" deleted successfully.',
            'scope': scope["label"],
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

__all__ = [
    "create_baseline",
    "restore_baseline",
    "get_baseline_info",
    "create_scenario",
    "list_scenarios",
    "restore_scenario",
    "rename_scenario",
    "delete_scenario",
]
