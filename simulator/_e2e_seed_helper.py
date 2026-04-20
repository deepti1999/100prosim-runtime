"""Helper shared by simulator/test_e2e_ui_*.py — loads a filtered seed fixture.

The bundled `seed/sqlite_seed.json` includes `admin.logentry` rows whose
`content_type_id` FKs reference IDs that don't match the test DB's freshly
migrated `django_content_type` table, which causes IntegrityError when loaddata
runs on SQLite. We strip those entries (they aren't needed for UI tests) and
feed the reduced fixture through loaddata via a tempfile.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from django.core.management import call_command

_SKIP_MODEL_PREFIXES = ("admin.",)  # add more here if further FK conflicts surface

_REPO = Path(__file__).resolve().parent.parent
_SEED = _REPO / "seed" / "sqlite_seed.json"


def load_e2e_seed() -> None:
    with _SEED.open(encoding="utf-8") as fh:
        rows = json.load(fh)
    filtered = [r for r in rows if not r.get("model", "").startswith(_SKIP_MODEL_PREFIXES)]

    tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    try:
        json.dump(filtered, tmp)
        tmp.close()
        call_command("loaddata", tmp.name, verbosity=0)
    finally:
        os.unlink(tmp.name)
