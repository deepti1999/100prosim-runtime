"""User-facing full provenance/reference sheet."""

from __future__ import annotations

import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from simulator.models import GebaeudewaermeData, LandUse, RenewableData, VerbrauchData
from simulator.ui_provenance_service import load_ui_provenance_override_map, payload_for_row


DOMAIN_CONFIG = [
    ("landuse", "Flächennutzung", LandUse, "name"),
    ("renewable", "Erneuerbare Energien", RenewableData, "name"),
    ("verbrauch", "Verbrauch", VerbrauchData, "category"),
    ("gebaeudewaerme", "Gebäudewärme", GebaeudewaermeData, "category"),
]


def _natural_code_key(code: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", str(code))]


def _has_provenance(payload: dict) -> bool:
    return bool(
        payload.get("source_url")
        or payload.get("notes_assumption")
        or payload.get("source_refs")
        or payload.get("origin") in {"d_xlsx", "derived"}
    )


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
