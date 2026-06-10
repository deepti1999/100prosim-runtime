"""Shared UI-only provenance overlay helpers.

These overrides are presentation metadata only. They intentionally do
not participate in calculations, cascades, worker jobs, or imports.
Views may overlay them onto the existing provenance fields when present.
"""

from __future__ import annotations

import re
from typing import Iterable

from simulator.models import UIProvenanceOverride


_STATUS_PREFIX_RE = re.compile(r"^\s*-?\s*STATUS-Ansatz:\s*", re.IGNORECASE)
_ZIEL_PREFIX_RE = re.compile(r"^\s*-?\s*ZIEL-Ansatz:\s*", re.IGNORECASE)
_ADMIN_ONLY_DOMAINS = {"landuse", "renewable", "verbrauch"}


def split_notes_assumption_sections(notes_assumption: str | None) -> dict[str, str]:
    """Split the current UI note text into general/status/ziel parts.

    Existing imported Excel notes are stored as one combined text blob.
    The admin override model stores these as separate editable fields.
    """
    result = {"general_information": "", "status_information": "", "ziel_information": ""}
    if not notes_assumption:
        return result

    current_key = "general_information"
    parts = {"general_information": [], "status_information": [], "ziel_information": []}
    for raw_part in str(notes_assumption).split("\n\n"):
        part = raw_part.strip()
        if not part:
            continue
        if _STATUS_PREFIX_RE.match(part):
            current_key = "status_information"
            part = _STATUS_PREFIX_RE.sub("", part).strip()
        elif _ZIEL_PREFIX_RE.match(part):
            current_key = "ziel_information"
            part = _ZIEL_PREFIX_RE.sub("", part).strip()
        parts[current_key].append(part)

    for key, values in parts.items():
        result[key] = "\n\n".join(values).strip()
    return result


def _build_payload(override: UIProvenanceOverride) -> dict:
    refs = override.build_source_refs()
    return {
        "source_url": override.primary_source_url(),
        "notes_assumption": override.build_notes_assumption() or None,
        "source_refs": refs,
        "is_override": True,
    }


def load_ui_provenance_override_map(domain: str, rows: Iterable[object]) -> dict[tuple[int, str], dict]:
    rows = list(rows)
    if not rows:
        return {}

    region_ids = {getattr(row, "region_id", None) for row in rows if getattr(row, "region_id", None)}
    codes = {getattr(row, "code", None) for row in rows if getattr(row, "code", None)}
    if not region_ids or not codes:
        return {}

    overrides = (
        UIProvenanceOverride.objects.filter(
            is_active=True,
            domain=domain,
            region_id__in=region_ids,
            row_code__in=codes,
        )
        .prefetch_related("sources")
    )
    return {(override.region_id, override.row_code): _build_payload(override) for override in overrides}


def apply_ui_provenance_to_objects(rows: Iterable[object], domain: str) -> None:
    rows = list(rows)
    override_map = load_ui_provenance_override_map(domain, rows)
    for row in rows:
        payload = override_map.get((getattr(row, "region_id", None), getattr(row, "code", None)))
        if not payload:
            continue
        row.source_url = payload["source_url"]
        row.notes_assumption = payload["notes_assumption"]
        row.source_refs = payload["source_refs"]
        row.provenance_override_active = True


def payload_for_row(row: object, domain: str, override_map: dict | None = None) -> dict:
    if override_map is None:
        override_map = load_ui_provenance_override_map(domain, [row])
    payload = override_map.get((getattr(row, "region_id", None), getattr(row, "code", None)))
    if domain in _ADMIN_ONLY_DOMAINS and not payload:
        return {
            "source_url": None,
            "notes_assumption": None,
            "source_refs": [],
            "origin": None,
            "provenance_override_active": False,
        }
    return {
        "source_url": payload["source_url"] if payload else getattr(row, "source_url", None),
        "notes_assumption": payload["notes_assumption"] if payload else getattr(row, "notes_assumption", None),
        "source_refs": payload["source_refs"] if payload else getattr(row, "source_refs", None),
        "origin": getattr(row, "origin", None),
        "provenance_override_active": bool(payload),
    }
