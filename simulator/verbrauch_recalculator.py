import logging
import re
from typing import Optional, List

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

def _hierarchy_depth(code: str) -> int:
    """Return hierarchy depth based on dot count (more dots = deeper)."""
    return code.count(".")

ALWAYS_RECALC_CODES = {"1"}  # top-level rollups that should be recalculated even if not flagged

def _materially_changed(old_value, new_value, rel_tol=1e-12) -> bool:
    if new_value is None:
        return False
    if old_value is None:
        return True
    delta = abs(float(old_value) - float(new_value))
    scale = max(1.0, abs(float(old_value)), abs(float(new_value)))
    return delta > (rel_tol * scale)

def _update_verbrauch_lookups(code: str, status_value, ziel_value, status_lookup, target_lookup) -> None:
    """Keep Verbrauch lookup aliases in sync for downstream formula evaluation."""
    dot_key = f"Verbrauch_{code}"
    underscore_key = f"Verbrauch_{code.replace('.', '_')}"
    status_lookup[dot_key] = float(status_value or 0)
    status_lookup[underscore_key] = float(status_value or 0)
    target_lookup[dot_key] = float(ziel_value or 0)
    target_lookup[underscore_key] = float(ziel_value or 0)

def _propagate_renewable_dependents_for_verbrauch_codes(changed_codes: List[str]) -> None:
    """
    Recalculate renewable rows affected by changed Verbrauch codes once per pass.

    This preserves the existing downstream renewable cascade but avoids
    recalculating the same renewable rows repeatedly for every changed
    Verbrauch row in the same pass.
    """
    if not changed_codes:
        return

    from calculation_engine.renewable_engine import RenewableCalculator
    from simulator.models import VerbrauchData, RenewableData, LandUse

    patterns = [
        re.compile(re.escape(f"VerbrauchData_{code}"))
        for code in changed_codes
    ]

    dependent_items = list(
        RenewableData.objects.filter(
            is_fixed=False,
            formula__isnull=False,
        )
    )
    items_to_update = [
        item for item in dependent_items
        if item.formula and any(pattern.search(item.formula) for pattern in patterns)
    ]
    if not items_to_update:
        return

    calculator = RenewableCalculator()
    landuse_data = {
        row.code: {'status_ha': row.status_ha or 0, 'target_ha': row.target_ha or 0}
        for row in LandUse.objects.all()
    }
    verbrauch_data = {
        row.code: {'status': row.status or 0, 'ziel': row.ziel or 0}
        for row in VerbrauchData.objects.all()
    }
    renewable_data = {
        row.code: {'status_value': row.status_value or 0, 'target_value': row.target_value or 0}
        for row in RenewableData.objects.all()
    }
    calculator.set_data_sources(landuse_data, verbrauch_data, renewable_data)

    for item in items_to_update:
        try:
            calc_status, calc_target = calculator.calculate(item.code)
            if calc_status is None and calc_target is None:
                continue

            status_changed = calc_status is not None and abs((item.status_value or 0) - calc_status) > 0.01
            target_changed = calc_target is not None and abs((item.target_value or 0) - calc_target) > 0.01
            if not (status_changed or target_changed):
                continue

            if calc_status is not None:
                item.status_value = calc_status
            if calc_target is not None:
                item.target_value = calc_target

            super(RenewableData, item).save(update_fields=['status_value', 'target_value', 'updated_at'])
            item._recalculate_dependents()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Renewable recalc from Verbrauch failed",
                extra={
                    "eventType": "validation",
                    "context": {"affected_code": item.code, "changed_verbrauch_codes": changed_codes},
                },
                exc_info=exc,
            )

def recalc_all_verbrauch(trigger_code: Optional[str] = None, propagate_renewables: bool = True) -> List[str]:
    """
    Recalculate all calculated VerbrauchData rows in dependency-safe order.

    - Processes deeper hierarchy items first so parents see fresh child values.
    - Uses one shared calculator/lookup set for performance.
    - Persists changed rows in bulk.
    - Returns list of codes that were updated.
    """
    # Local import to avoid circular dependency
    from calculation_engine.verbrauch_engine import VerbrauchCalculator
    from simulator.models import VerbrauchData, RenewableData, LandUse, Formula

    updated_codes: list[str] = []
    with transaction.atomic():
        items = list(VerbrauchData.objects.all().order_by("-code"))
        # Sort by depth desc so children calculate before parents
        items.sort(key=lambda i: _hierarchy_depth(i.code), reverse=True)

        verbrauch_data = {
            row.code: {
                'status': row.status or 0,
                'ziel': row.ziel or 0,
            }
            for row in items
        }
        renewable_data = {
            row.code: {
                'status_value': row.status_value or 0,
                'target_value': row.target_value or 0,
            }
            for row in RenewableData.objects.all()
        }
        landuse_data = {
            row.code: {
                'status_ha': row.status_ha or 0,
                'target_ha': row.target_ha or 0,
            }
            for row in LandUse.objects.all()
        }

        calculator = VerbrauchCalculator()
        formula_map = {
            f.key: f
            for f in Formula.objects.filter(category='verbrauch', is_active=True).prefetch_related('variables')
        }
        calculator._formula_cache = dict(formula_map)
        calculator._target_formula_cache = {
            key: formula
            for key, formula in formula_map.items()
            if key.endswith('_ziel') or key.endswith('_target')
        }
        calculator.set_data_sources(verbrauch_data, renewable_data, landuse_data)
        status_lookup = calculator.evaluator.status_lookup
        target_lookup = calculator.evaluator.target_lookup

        changed_items = []
        updated_item_map = {}
        for item in items:
            if not (
                item.is_calculated
                or item.status_calculated
                or item.ziel_calculated
                or item.code in ALWAYS_RECALC_CODES
            ):
                continue

            new_status = item.status
            new_ziel = item.ziel

            try:
                if item.status_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    calc_status, calc_ziel = calculator.calculate(item.code)
                    if calc_status is not None:
                        new_status = calc_status
                    if item.ziel_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                        if calc_ziel is not None:
                            new_ziel = calc_ziel
                if item.ziel_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES:
                    if not (item.status_calculated or item.is_calculated or item.code in ALWAYS_RECALC_CODES):
                        _, calc_ziel = calculator.calculate(item.code)
                        if calc_ziel is not None:
                            new_ziel = calc_ziel
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Verbrauch recalculation failed",
                    extra={
                        "eventType": "validation",
                        "context": {
                            "code": item.code,
                            "trigger_code": trigger_code,
                        },
                    },
                    exc_info=exc,
                )
                continue

            changed = False
            if _materially_changed(item.status, new_status):
                item.status = new_status
                changed = True
            if _materially_changed(item.ziel, new_ziel):
                item.ziel = new_ziel
                changed = True

            if changed:
                updated_codes.append(item.code)
                changed_items.append(item)
                updated_item_map[item.code] = item

                verbrauch_data[item.code] = {
                    'status': item.status or 0,
                    'ziel': item.ziel or 0,
                }
                _update_verbrauch_lookups(
                    item.code,
                    item.status,
                    item.ziel,
                    status_lookup,
                    target_lookup,
                )
                calculator.cache[f"V_{item.code}"] = (item.status, item.ziel)

        if changed_items:
            now = timezone.now()
            for row in changed_items:
                row.updated_at = now
            VerbrauchData.objects.bulk_update(changed_items, ['status', 'ziel', 'updated_at'])

        if propagate_renewables:
            _propagate_renewable_dependents_for_verbrauch_codes(updated_codes)

    return updated_codes
