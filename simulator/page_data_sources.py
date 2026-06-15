"""User-facing full provenance/reference sheet."""

from __future__ import annotations

import re

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from simulator.models import GebaeudewaermeData, LandUse, RenewableData, VerbrauchData
from simulator.ui_provenance_service import (
    load_ui_provenance_override_map,
    payload_for_row,
    split_notes_assumption_sections,
)


DOMAIN_CONFIG = [
    ("landuse", "Flächennutzung", LandUse, "name"),
    ("renewable", "Erneuerbare Energien", RenewableData, "name"),
    ("verbrauch", "Verbrauch", VerbrauchData, "category"),
    ("gebaeudewaerme", "Gebäudewärme", GebaeudewaermeData, "category"),
]
DOMAIN_CONFIG_BY_KEY = {
    domain: {
        "title": title,
        "model": model,
        "label_field": label_field,
    }
    for domain, title, model, label_field in DOMAIN_CONFIG
}


def _natural_code_key(code: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", str(code))]


def _has_provenance(payload: dict) -> bool:
    return bool(
        payload.get("source_url")
        or payload.get("notes_assumption")
        or payload.get("source_refs")
        or payload.get("origin") in {"d_xlsx", "derived"}
    )


def _row_display_values(row: object, domain: str) -> dict[str, object]:
    if domain == "landuse":
        return {"status": getattr(row, "status_ha", None), "ziel": getattr(row, "target_ha", None)}
    if domain == "renewable":
        return {"status": getattr(row, "status_value", None), "ziel": getattr(row, "target_value", None)}
    return {"status": getattr(row, "status", None), "ziel": getattr(row, "ziel", None)}


def _source_refs_by_section(source_refs: list[dict]) -> dict[str, list[dict]]:
    sections = {"general": [], "status": [], "ziel": []}
    for ref in source_refs or []:
        section = ref.get("section") or "general"
        sections.setdefault(section, []).append(ref)
    return sections


@login_required
def data_sources_view(request):
    sections = []
    for domain, title, model, label_field in DOMAIN_CONFIG:
        rows = list(model.objects.all())
        provenance_map = load_ui_provenance_override_map(domain, rows)
        items = []

        for row in rows:
            payload = payload_for_row(row, domain, provenance_map)
            if not _has_provenance(payload):
                continue
            items.append(
                {
                    "code": row.code,
                    "label": getattr(row, label_field, ""),
                    "notes_assumption": payload["notes_assumption"],
                    "source_refs": payload["source_refs"] or [],
                    "source_url": payload["source_url"],
                    "origin": payload["origin"],
                    "provenance_override_active": payload["provenance_override_active"],
                }
            )

        items.sort(key=lambda item: _natural_code_key(item["code"]))
        sections.append(
            {
                "domain": domain,
                "title": title,
                "items": items,
            }
        )

    return render(
        request,
        "simulator/data_sources.html",
        {
            "sections": sections,
            "current_section": "data_sources",
        },
    )


@login_required
def data_source_detail_view(request, domain: str, row_code: str):
    config = DOMAIN_CONFIG_BY_KEY.get(domain)
    if not config:
        raise Http404("Unbekannter Datenbereich")

    rows = config["model"].objects.filter(code=row_code)
    region_id = request.GET.get("region_id")
    if region_id:
        rows = rows.filter(region_id=region_id)
    row = rows.first()
    if row is None:
        raise Http404("Datenzeile nicht gefunden")

    payload = payload_for_row(row, domain, load_ui_provenance_override_map(domain, [row]))
    source_refs = payload.get("source_refs") or []
    sections = split_notes_assumption_sections(payload.get("notes_assumption"))

    return render(
        request,
        "simulator/data_source_detail.html",
        {
            "current_section": "data_sources",
            "domain": domain,
            "domain_title": config["title"],
            "row": row,
            "row_code": row.code,
            "row_label": getattr(row, config["label_field"], ""),
            "row_values": _row_display_values(row, domain),
            "source_url": payload.get("source_url"),
            "source_refs_by_section": _source_refs_by_section(source_refs),
            "general_information": sections["general_information"],
            "status_information": sections["status_information"],
            "ziel_information": sections["ziel_information"],
            "notes_assumption": payload.get("notes_assumption"),
            "show_primary_source_url": bool(payload.get("source_url") and not source_refs),
            "has_provenance": _has_provenance(payload),
            "provenance_override_active": payload.get("provenance_override_active"),
        },
    )
