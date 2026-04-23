"""Phase A §2.3 — import provenance (source URL + assumption text + origin)
from D.xlsx into the 4 parameter-bearing models.

Strict invariants enforced (per CLAUDE.md + DATA_MODEL_IMPORT_AUDIT.md):
  - SR-005: per-user workspace rows (owner != NULL) NEVER touched.
  - SR-007: no `code` field rename; ONLY source_url, notes_assumption,
            origin are written.
  - HARD: no value column (status_ha, target_ha, status, ziel, status_value,
          target_value) is touched. Phase A is provenance-only.
  - D3: fail loud on missing file, non-xlsx, or unrecognised sheet schema.
  - D5: write manifest + orphan-classification CSV after --apply.

Output artefacts on --apply:
  - data/import/d_xlsx.manifest.json — file hash + per-sheet hashes + counters.
  - data/import/orphan_classification.csv — every unmatched row with rationale.

Usage:
  python manage.py import_excel_provenance docs/100prosim_d_*/D.xlsx          # dry-run
  python manage.py import_excel_provenance docs/100prosim_d_*/D.xlsx --apply  # commit
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from openpyxl import load_workbook

from simulator.models import (
    GebaeudewaermeData,
    LandUse,
    RenewableData,
    VerbrauchData,
)


REQUIRED_SHEETS = ("1.", "9.Quellen")

# Row-type column on D.xlsx 1. (col 67 = "BO" — single letter row classifier)
TYPE_COL = 67
LABEL_COL = 5
VALUE_COL_W = 23

PARAMETER_TYPE = "p"
ASSUMPTION_TYPES = ("e", "s", "z", "h")  # erläuterung / status-Ansatz / ziel-Ansatz / herleitung

# Source URL refs inside assumption text look like [9.123] or [9.123.4]
SOURCE_REF_RE = re.compile(r"\[(9\.\d+(?:\.\d+)?)\]")


class _ModelPlan:
    def __init__(self, model, label_field: str, code_field: str):
        self.model = model
        self.label_field = label_field
        self.code_field = code_field


MODEL_PLANS = [
    _ModelPlan(LandUse, label_field="name", code_field="code"),
    _ModelPlan(RenewableData, label_field="name", code_field="code"),
    _ModelPlan(VerbrauchData, label_field="category", code_field="code"),
    _ModelPlan(GebaeudewaermeData, label_field="category", code_field="code"),
]


def _normalize_label(s: Optional[str]) -> str:
    """Lower-case, strip parens / asterisks / hyphens, collapse whitespace."""
    if not s:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"[\*]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


class Command(BaseCommand):
    help = (
        "Phase A §2.3: import provenance (source URL + assumption text + origin) "
        "from D.xlsx into LandUse / RenewableData / VerbrauchData / GebaeudewaermeData."
    )

    def add_arguments(self, parser):
        parser.add_argument("xlsx_path", help="Path to D.xlsx (gitignored).")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Commit changes. Without this, runs in dry-run mode and prints the diff only.",
        )
        parser.add_argument(
            "--region",
            default="DE",
            help="Region code recorded in the manifest (Phase A is DE-only).",
        )

    # ------------------------------------------------------------------
    # entry
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        xlsx_path = options["xlsx_path"]
        apply_changes = options["apply"]
        region = options["region"]

        self._validate_file(xlsx_path)

        try:
            wb = load_workbook(xlsx_path, data_only=True, read_only=False)
        except Exception as e:
            raise CommandError(f"Failed to open {xlsx_path}: {e}")

        for sheet in REQUIRED_SHEETS:
            if sheet not in wb.sheetnames:
                raise CommandError(
                    f"D.xlsx schema mismatch: required sheet '{sheet}' not found. "
                    f"Got sheets: {wb.sheetnames}"
                )

        sources = self._extract_sources(wb["9.Quellen"])
        self.stdout.write(self.style.SUCCESS(f"Extracted {len(sources)} source URLs from 9.Quellen"))

        d1_index = self._build_d1_index(wb["1."])
        self.stdout.write(self.style.SUCCESS(f"Indexed {len(d1_index)} parameter rows in D.xlsx '1.'"))

        diffs = []
        for plan in MODEL_PLANS:
            d = self._compute_diff(plan, d1_index, sources)
            diffs.append(d)

        # Summary
        total_changed = sum(d["changed"] for d in diffs)
        for d in diffs:
            self.stdout.write(
                f"  {d['model_name']:24s}  total={d['total']:4d}  "
                f"matched={d['matched']:4d}  unmatched={d['unmatched']:4d}  "
                f"changed={d['changed']:4d}"
            )
        self.stdout.write(
            self.style.SUCCESS(f"Total: {total_changed} changed across {len(diffs)} models")
        )

        if apply_changes:
            with transaction.atomic():
                for d, plan in zip(diffs, MODEL_PLANS):
                    self._apply_diff(plan.model, d)
            self._write_manifest(xlsx_path, region, diffs)
            self._write_orphan_csv(diffs)
            self.stdout.write(self.style.SUCCESS("APPLIED."))
        else:
            self.stdout.write(self.style.WARNING("dry-run only — pass --apply to commit"))

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------

    def _validate_file(self, xlsx_path: str) -> None:
        if not os.path.isfile(xlsx_path):
            raise CommandError(f"File not found: {xlsx_path}")
        if not xlsx_path.lower().endswith((".xlsx", ".xlsm")):
            raise CommandError(f"Not an .xlsx/.xlsm file: {xlsx_path}")
        try:
            with open(xlsx_path, "rb") as f:
                magic = f.read(4)
        except Exception as e:
            raise CommandError(f"Cannot read {xlsx_path}: {e}")
        if magic != b"PK\x03\x04":
            raise CommandError(f"Not a valid xlsx (zip magic missing): {xlsx_path}")

    # ------------------------------------------------------------------
    # extractors
    # ------------------------------------------------------------------

    def _extract_sources(self, ws) -> dict[str, str]:
        """Build {ref_code: url} from 9.Quellen.

        Layout (verified by scripts/audit_out/workbook_catalog.txt):
          col 1 = D-prefixed code (e.g. 'D.9.5')
          col 2 = bare ref code (e.g. '9.5')
          col 4 = URL hyperlink target
        """
        sources: dict[str, str] = {}
        for r in range(1, ws.max_row + 1):
            ref_code = ws.cell(row=r, column=2).value
            if not isinstance(ref_code, str) or not ref_code.strip():
                continue
            ref_code = ref_code.strip()
            cell_url = ws.cell(row=r, column=4)
            url: Optional[str] = None
            if cell_url.hyperlink and cell_url.hyperlink.target:
                url = cell_url.hyperlink.target
            elif isinstance(cell_url.value, str) and cell_url.value.startswith(("http://", "https://")):
                url = cell_url.value
            if url:
                sources[ref_code] = url
        return sources

    def _build_d1_index(self, ws) -> dict[str, dict]:
        """Build {normalized_label: {row, label, assumption_text, value_w}} from D.xlsx '1.'.

        For each parameter (type='p') row, gather adjacent assumption rows
        (type in 'e','s','z','h') until the next 'p' row, and concat their
        col-E text as the assumption_text.
        """
        index: dict[str, dict] = {}
        # First pass: collect all (row, type, label, w_value) tuples
        rows: list[tuple[int, Optional[str], Optional[str], object]] = []
        for r in range(1, ws.max_row + 1):
            t = ws.cell(row=r, column=TYPE_COL).value
            label = ws.cell(row=r, column=LABEL_COL).value
            w = ws.cell(row=r, column=VALUE_COL_W).value
            if label is None and t is None:
                continue
            rows.append((r, t, label, w))

        # Second pass: for each parameter row, gather assumption rows beneath
        for i, (r, t, label, w) in enumerate(rows):
            if t != PARAMETER_TYPE:
                continue
            if not isinstance(label, str) or not label.strip():
                continue
            assumption_parts: list[str] = []
            for j in range(i + 1, len(rows)):
                rj, tj, lj, wj = rows[j]
                if tj == PARAMETER_TYPE:
                    break
                if tj in ASSUMPTION_TYPES and isinstance(lj, str) and lj.strip():
                    assumption_parts.append(lj.strip())
            assumption_text = "\n\n".join(assumption_parts) if assumption_parts else None

            norm = _normalize_label(label)
            # If label collision, keep the first seen (prefer earlier definition)
            if norm and norm not in index:
                index[norm] = {
                    "row": r,
                    "label": label.strip(),
                    "assumption_text": assumption_text,
                    "value_w": w,
                }

        return index

    # ------------------------------------------------------------------
    # diff + apply
    # ------------------------------------------------------------------

    def _compute_diff(self, plan: _ModelPlan, d1_index: dict, sources: dict) -> dict:
        model = plan.model
        # SR-005: ONLY base rows (owner=NULL); never touch user workspace.
        if hasattr(model, "all_objects"):
            qs = model.all_objects.all()
            # Filter for owner=NULL where the model has owner field
            if any(f.name == "owner" for f in model._meta.get_fields()):
                qs = model.all_objects.filter(owner__isnull=True)
        else:
            qs = model.objects.all()

        rows = list(qs)

        diff = {
            "model_name": model.__name__,
            "total": len(rows),
            "matched": 0,
            "unmatched": 0,
            "changed": 0,
            "updates": [],
            "orphans": [],
        }

        for row in rows:
            label = getattr(row, plan.label_field, None) or ""
            norm = _normalize_label(label)
            entry = d1_index.get(norm)

            new_source_url: Optional[str] = None
            new_notes_assumption: Optional[str] = None
            new_origin = "internal"
            orphan_reason: Optional[str] = None

            if entry:
                new_origin = "d_xlsx"
                new_notes_assumption = entry["assumption_text"]
                if new_notes_assumption:
                    refs = SOURCE_REF_RE.findall(new_notes_assumption)
                    for ref in refs:
                        if ref in sources:
                            new_source_url = sources[ref]
                            break
                diff["matched"] += 1
            else:
                diff["unmatched"] += 1
                orphan_reason = "no D.xlsx 1. parameter row matches normalized label"
                diff["orphans"].append(
                    (getattr(row, plan.code_field, ""), label, orphan_reason)
                )

            current = (row.source_url, row.notes_assumption, row.origin)
            new = (new_source_url, new_notes_assumption, new_origin)
            if current != new:
                diff["changed"] += 1
                diff["updates"].append(
                    {
                        "pk": row.pk,
                        "code": getattr(row, plan.code_field, ""),
                        "source_url": new_source_url,
                        "notes_assumption": new_notes_assumption,
                        "origin": new_origin,
                    }
                )

        return diff

    def _apply_diff(self, model, diff: dict) -> None:
        """Write only the 3 provenance columns via QuerySet.update() —
        bypasses signals so cache invalidation isn't triggered (provenance
        does not affect calculations)."""
        for upd in diff["updates"]:
            if hasattr(model, "all_objects"):
                qs = model.all_objects.filter(pk=upd["pk"])
            else:
                qs = model.objects.filter(pk=upd["pk"])
            qs.update(
                source_url=upd["source_url"],
                notes_assumption=upd["notes_assumption"],
                origin=upd["origin"],
            )

    # ------------------------------------------------------------------
    # artefacts
    # ------------------------------------------------------------------

    def _write_manifest(self, xlsx_path: str, region: str, diffs: list[dict]) -> None:
        out_dir = Path("data/import")
        out_dir.mkdir(parents=True, exist_ok=True)

        with open(xlsx_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # Per-sheet content hash (cheap fingerprint over cell values)
        wb = load_workbook(xlsx_path, data_only=True, read_only=True)
        sheet_hashes: dict[str, str] = {}
        for sn in REQUIRED_SHEETS:
            if sn in wb.sheetnames:
                ws = wb[sn]
                blob = []
                row_count = 0
                for row in ws.iter_rows(values_only=True):
                    blob.append("|".join(str(v) if v is not None else "" for v in row))
                    row_count += 1
                    if row_count >= 5000:
                        break
                sheet_hashes[sn] = hashlib.sha256("\n".join(blob).encode("utf-8")).hexdigest()

        manifest = {
            "import_tool_version": "1.0.0",
            "import_date": datetime.now(timezone.utc).isoformat(),
            "files": [
                {
                    "path": os.path.basename(xlsx_path),
                    "file_hash": f"sha256:{file_hash}",
                    "sheet_hashes": {k: f"sha256:{v}" for k, v in sheet_hashes.items()},
                    "region_code": region,
                    "rows_imported": sum(d["total"] for d in diffs),
                    "rows_matched": sum(d["matched"] for d in diffs),
                    "rows_unmatched": sum(d["unmatched"] for d in diffs),
                    "rows_changed": sum(d["changed"] for d in diffs),
                    "per_model": [
                        {
                            "model": d["model_name"],
                            "total": d["total"],
                            "matched": d["matched"],
                            "unmatched": d["unmatched"],
                            "changed": d["changed"],
                        }
                        for d in diffs
                    ],
                }
            ],
        }

        path = out_dir / "d_xlsx.manifest.json"
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote manifest: {path}"))

    def _write_orphan_csv(self, diffs: list[dict]) -> None:
        out_dir = Path("data/import")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "orphan_classification.csv"
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["model", "code", "label", "origin", "rationale"])
            for d in diffs:
                for code, label, reason in d["orphans"]:
                    w.writerow([d["model_name"], code, label, "internal", reason])
        self.stdout.write(self.style.SUCCESS(f"Wrote orphan CSV: {path}"))
