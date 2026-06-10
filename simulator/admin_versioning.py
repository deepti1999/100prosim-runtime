from __future__ import annotations

import json
from typing import Any

from django.db import transaction
from django.utils import timezone

from simulator.models import (
    CategoryDisplayName,
    Formula,
    FormulaVariable,
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    UIProvenanceOverride,
    UIProvenanceSource,
    VerbrauchData,
)
from simulator.ws_models import WS365Formula, WSData


SCHEMA_VERSION = 1


def _manager(model):
    return getattr(model, "all_objects", model.objects)


def _has_field(model, field_name: str) -> bool:
    return any(f.name == field_name for f in model._meta.concrete_fields)


def _global_qs(model, region: Region | None = None):
    qs = _manager(model).all()
    if _has_field(model, "owner"):
        qs = qs.filter(owner__isnull=True)
    if region is not None and _has_field(model, "region"):
        qs = qs.filter(region=region)
    return qs


def _plain_fields(model, extra_exclude: set[str] | None = None) -> list[str]:
    exclude = {"id", "owner", "region", "created_at", "updated_at"}
    exclude.update(extra_exclude or set())
    return [f.name for f in model._meta.concrete_fields if f.name not in exclude]


def _serialize_rows(model, region: Region | None = None, *, order_by: str = "id") -> list[dict[str, Any]]:
    fields = _plain_fields(model)
    rows = []
    for obj in _global_qs(model, region).order_by(order_by):
        rows.append({field: getattr(obj, field) for field in fields})
    return rows


def _delete_global_rows(model, region: Region | None = None) -> None:
    qs = _global_qs(model, region)
    if qs.exists():
        qs._raw_delete(qs.db)


def _restore_rows(model, rows: list[dict[str, Any]], region: Region | None = None) -> int:
    _delete_global_rows(model, region)
    if not rows:
        return 0
    allowed = set(_plain_fields(model))
    objects = []
    for row in rows:
        payload = {key: value for key, value in row.items() if key in allowed}
        if _has_field(model, "owner"):
            payload["owner"] = None
        if region is not None and _has_field(model, "region"):
            payload["region"] = region
        objects.append(model(**payload))
    _manager(model).bulk_create(objects, batch_size=1000)
    return len(objects)


def _serialize_landuse(region: Region) -> list[dict[str, Any]]:
    rows = []
    for obj in _global_qs(LandUse, region).order_by("id"):
        rows.append(
            {
                "code": obj.code,
                "name": obj.name,
                "status_ha": obj.status_ha,
                "target_ha": obj.target_ha,
                "status_formula_key": obj.status_formula_key,
                "target_formula_key": obj.target_formula_key,
                "user_percent": obj.user_percent,
                "increase_limit_baseline_percent": obj.increase_limit_baseline_percent,
                "target_locked": obj.target_locked,
                "quelle": obj.quelle,
                "source_url": obj.source_url,
                "notes_assumption": obj.notes_assumption,
                "source_refs": obj.source_refs,
                "origin": obj.origin,
                "parent_code": obj.parent.code if obj.parent else None,
            }
        )
    return rows


def _restore_landuse(rows: list[dict[str, Any]], region: Region) -> int:
    _delete_global_rows(LandUse, region)
    if not rows:
        return 0

    objects = []
    for row in rows:
        objects.append(
            LandUse(
                owner=None,
                region=region,
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
                source_url=row.get("source_url"),
                notes_assumption=row.get("notes_assumption"),
                source_refs=row.get("source_refs") or [],
                origin=row.get("origin") or "internal",
                parent=None,
            )
        )
    LandUse.all_objects.bulk_create(objects, batch_size=1000)

    created = list(_global_qs(LandUse, region).order_by("id"))
    by_code = {obj.code: obj for obj in created}
    updates = []
    for row in rows:
        child = by_code.get(row.get("code"))
        parent = by_code.get(row.get("parent_code"))
        if child and parent:
            child.parent = parent
            updates.append(child)
    if updates:
        LandUse.all_objects.bulk_update(updates, ["parent"])
    return len(objects)


def _serialize_formulas() -> list[dict[str, Any]]:
    fields = _plain_fields(Formula, {"last_validated"})
    return [
        {field: getattr(obj, field) for field in fields}
        for obj in Formula.objects.order_by("category", "key", "id")
    ]


def _serialize_formula_variables() -> list[dict[str, Any]]:
    rows = []
    for obj in FormulaVariable.objects.select_related("formula").order_by("formula__key", "variable_name"):
        rows.append(
            {
                "formula_key": obj.formula.key,
                "variable_name": obj.variable_name,
                "source_type": obj.source_type,
                "source_key": obj.source_key,
                "default_value": obj.default_value,
                "is_required": obj.is_required,
                "notes": obj.notes,
            }
        )
    return rows


def _restore_formulas(formulas: list[dict[str, Any]], variables: list[dict[str, Any]]) -> int:
    FormulaVariable.objects.all().delete()
    Formula.objects.all().delete()
    Formula.objects.bulk_create([Formula(**row) for row in formulas], batch_size=1000)
    formula_by_key = {obj.key: obj for obj in Formula.objects.all()}
    variable_objects = []
    for row in variables:
        formula = formula_by_key.get(row.get("formula_key"))
        if not formula:
            continue
        variable_objects.append(
            FormulaVariable(
                formula=formula,
                variable_name=row.get("variable_name"),
                source_type=row.get("source_type"),
                source_key=row.get("source_key"),
                default_value=row.get("default_value"),
                is_required=bool(row.get("is_required", True)),
                notes=row.get("notes") or "",
            )
        )
    FormulaVariable.objects.bulk_create(variable_objects, batch_size=1000)
    return len(formulas)


def _serialize_ui_provenance(region: Region) -> list[dict[str, Any]]:
    rows = []
    for obj in UIProvenanceOverride.objects.filter(region=region).order_by("domain", "row_code", "id"):
        rows.append(
            {
                "domain": obj.domain,
                "row_code": obj.row_code,
                "row_label": obj.row_label,
                "general_information": obj.general_information,
                "status_information": obj.status_information,
                "ziel_information": obj.ziel_information,
                "is_active": obj.is_active,
                "sources": [
                    {
                        "section": source.section,
                        "label": source.label,
                        "description": source.description,
                        "url": source.url,
                        "sort_order": source.sort_order,
                    }
                    for source in obj.sources.order_by("section", "sort_order", "id")
                ],
            }
        )
    return rows


def _restore_ui_provenance(rows: list[dict[str, Any]], region: Region) -> int:
    UIProvenanceOverride.objects.filter(region=region).delete()
    created_count = 0
    for row in rows:
        override = UIProvenanceOverride.objects.create(
            region=region,
            domain=row.get("domain"),
            row_code=row.get("row_code"),
            row_label=row.get("row_label") or "",
            general_information=row.get("general_information") or "",
            status_information=row.get("status_information") or "",
            ziel_information=row.get("ziel_information") or "",
            is_active=bool(row.get("is_active", True)),
        )
        UIProvenanceSource.objects.bulk_create(
            [
                UIProvenanceSource(
                    override=override,
                    section=source.get("section") or "general",
                    label=source.get("label") or "",
                    description=source.get("description") or "",
                    url=source.get("url") or "",
                    sort_order=source.get("sort_order") or 0,
                )
                for source in row.get("sources", [])
            ]
        )
        created_count += 1
    return created_count


def _resolve_region(region_code: str | None) -> Region:
    return Region.objects.get(code=region_code or "DE")


def capture_admin_version_payload(region_code: str = "DE") -> dict[str, Any]:
    region = _resolve_region(region_code)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": timezone.now().isoformat(),
        "region_code": region.code,
        "landuse": _serialize_landuse(region),
        "renewable": _serialize_rows(RenewableData, region, order_by="code"),
        "verbrauch": _serialize_rows(VerbrauchData, region, order_by="code"),
        "gebaeudewaerme": _serialize_rows(GebaeudewaermeData, region, order_by="code"),
        "ws": _serialize_rows(WSData, region, order_by="tag_im_jahr"),
        "formulas": _serialize_formulas(),
        "formula_variables": _serialize_formula_variables(),
        "ws365_formulas": _serialize_rows(WS365Formula, order_by="column_name"),
        "category_display_names": _serialize_rows(CategoryDisplayName, order_by="category_code"),
        "ui_provenance": _serialize_ui_provenance(region),
    }
    payload["counts"] = {
        key: len(value)
        for key, value in payload.items()
        if isinstance(value, list)
    }
    return payload


def restore_admin_version_payload(payload: dict[str, Any]) -> dict[str, int]:
    payload = payload or {}
    region = _resolve_region(payload.get("region_code") or "DE")
    with transaction.atomic():
        restored = {
            "landuse": _restore_landuse(payload.get("landuse", []), region),
            "renewable": _restore_rows(RenewableData, payload.get("renewable", []), region),
            "verbrauch": _restore_rows(VerbrauchData, payload.get("verbrauch", []), region),
            "gebaeudewaerme": _restore_rows(GebaeudewaermeData, payload.get("gebaeudewaerme", []), region),
            "ws": _restore_rows(WSData, payload.get("ws", []), region),
            "formulas": _restore_formulas(
                payload.get("formulas", []),
                payload.get("formula_variables", []),
            ),
            "ws365_formulas": _restore_rows(WS365Formula, payload.get("ws365_formulas", [])),
            "category_display_names": _restore_rows(
                CategoryDisplayName,
                payload.get("category_display_names", []),
            ),
            "ui_provenance": _restore_ui_provenance(payload.get("ui_provenance", []), region),
        }
    invalidate_admin_version_caches()
    return restored


def invalidate_admin_version_caches() -> None:
    try:
        from django.core.cache import cache

        cache.clear()
    except Exception:
        pass
    try:
        from simulator.recalc_cache import invalidate

        invalidate()
    except Exception:
        pass
    try:
        from simulator.formula_service import invalidate_auto_tokens_cache, invalidate_lookups_cache

        invalidate_auto_tokens_cache()
        invalidate_lookups_cache()
    except Exception:
        pass
    try:
        from simulator.ws365_orchestrator import invalidate_ws365_cache

        invalidate_ws365_cache()
    except Exception:
        pass


def payload_size_mb(payload: dict[str, Any]) -> float:
    return round(len(json.dumps(payload or {}, default=str).encode("utf-8")) / (1024 * 1024), 2)
