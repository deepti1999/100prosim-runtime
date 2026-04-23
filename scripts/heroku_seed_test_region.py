"""
Phase C V5 helper — clone DE base rows into TEST region with values × 1.05.

Run on Heroku via:
  heroku run -a prosim-100 "python scripts/heroku_seed_test_region.py"

Throwaway: gets deleted after Heroku V5 verification along with the TEST
region rows. Not used by the application or any test suite.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "landuse_project.settings")
django.setup()

from django.db import transaction  # noqa: E402

from simulator.models import (  # noqa: E402
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    VerbrauchData,
)
from simulator.ws_models import WSData  # noqa: E402


SCALE = 1.05


def _scale(v):
    return v * SCALE if v is not None else None


def main():
    de = Region.objects.get(code="DE")
    test_region, created = Region.objects.get_or_create(
        code="TEST",
        defaults={
            "display_name": "Phase C Smoke",
            "active": True,
            "installed_pmax_ely_gw": 200.0,
            "installed_pmax_rv_gw": 270.0,
        },
    )
    print(f"TEST region: {'created' if created else 'exists'} (pk={test_region.pk})")

    with transaction.atomic():
        # LandUse (re-link parents by code after bulk_create)
        de_lu = list(LandUse.all_objects.filter(owner__isnull=True, region=de).order_by("id"))
        existing_test_lu = LandUse.all_objects.filter(owner__isnull=True, region=test_region).count()
        if existing_test_lu == 0:
            clones = []
            for r in de_lu:
                clones.append(
                    LandUse(
                        code=r.code, name=r.name,
                        status_ha=_scale(r.status_ha), target_ha=_scale(r.target_ha),
                        status_formula_key=r.status_formula_key,
                        target_formula_key=r.target_formula_key,
                        user_percent=r.user_percent,
                        increase_limit_baseline_percent=r.increase_limit_baseline_percent,
                        target_locked=r.target_locked,
                        quelle=r.quelle,
                        source_url=r.source_url,
                        notes_assumption=r.notes_assumption,
                        origin=r.origin,
                        region=test_region,
                    )
                )
            LandUse.all_objects.bulk_create(clones, batch_size=1000)
            new_lu = LandUse.all_objects.filter(owner__isnull=True, region=test_region)
            by_code = {r.code: r for r in new_lu}
            updates = []
            for de_row in de_lu:
                if de_row.parent_id and de_row.code in by_code:
                    parent = de_row.parent
                    if parent and parent.code in by_code:
                        clone = by_code[de_row.code]
                        clone.parent_id = by_code[parent.code].id
                        updates.append(clone)
            if updates:
                LandUse.all_objects.bulk_update(updates, ["parent"])
            print(f"LandUse: cloned {len(clones)}")
        else:
            print(f"LandUse: skip (TEST already has {existing_test_lu} rows)")

        # RenewableData
        de_r = list(RenewableData.all_objects.filter(owner__isnull=True, region=de).order_by("id"))
        existing_test_r = RenewableData.all_objects.filter(owner__isnull=True, region=test_region).count()
        if existing_test_r == 0:
            clones = []
            for r in de_r:
                clones.append(
                    RenewableData(
                        code=r.code, category=r.category, subcategory=r.subcategory,
                        name=r.name, description=r.description, unit=r.unit,
                        status_value=_scale(r.status_value),
                        target_value=_scale(r.target_value),
                        user_input=r.user_input, user_editable=r.user_editable,
                        formula=r.formula, is_fixed=r.is_fixed, parent_code=r.parent_code,
                        source=r.source, notes=r.notes,
                        source_url=r.source_url, notes_assumption=r.notes_assumption, origin=r.origin,
                        region=test_region,
                    )
                )
            RenewableData.all_objects.bulk_create(clones, batch_size=1000)
            print(f"RenewableData: cloned {len(clones)}")
        else:
            print(f"RenewableData: skip (TEST already has {existing_test_r} rows)")

        # VerbrauchData
        de_v = list(VerbrauchData.all_objects.filter(owner__isnull=True, region=de).order_by("id"))
        existing_test_v = VerbrauchData.all_objects.filter(owner__isnull=True, region=test_region).count()
        if existing_test_v == 0:
            clones = []
            for r in de_v:
                clones.append(
                    VerbrauchData(
                        code=r.code, category=r.category, unit=r.unit,
                        status=_scale(r.status), ziel=_scale(r.ziel),
                        is_calculated=r.is_calculated,
                        status_calculated=r.status_calculated,
                        ziel_calculated=r.ziel_calculated,
                        user_percent=r.user_percent, user_editable=r.user_editable,
                        source_url=r.source_url, notes_assumption=r.notes_assumption, origin=r.origin,
                        region=test_region,
                    )
                )
            VerbrauchData.all_objects.bulk_create(clones, batch_size=1000)
            print(f"VerbrauchData: cloned {len(clones)}")
        else:
            print(f"VerbrauchData: skip (TEST already has {existing_test_v} rows)")

        # GebaeudewaermeData
        de_g = list(GebaeudewaermeData.all_objects.filter(region=de).order_by("id"))
        existing_test_g = GebaeudewaermeData.all_objects.filter(region=test_region).count()
        if existing_test_g == 0:
            clones = []
            for r in de_g:
                clones.append(
                    GebaeudewaermeData(
                        code=r.code, category=r.category, unit=r.unit,
                        status=_scale(r.status), ziel=_scale(r.ziel),
                        formula=r.formula,
                        is_calculated=r.is_calculated,
                        status_calculated=r.status_calculated,
                        ziel_calculated=r.ziel_calculated,
                        user_percent=r.user_percent,
                        source_url=r.source_url, notes_assumption=r.notes_assumption, origin=r.origin,
                        region=test_region,
                    )
                )
            GebaeudewaermeData.all_objects.bulk_create(clones, batch_size=1000)
            print(f"GebaeudewaermeData: cloned {len(clones)}")
        else:
            print(f"GebaeudewaermeData: skip (TEST already has {existing_test_g} rows)")

        # WSData (per-region 365-day series)
        de_ws = list(WSData.all_objects.filter(owner__isnull=True, region=de).order_by("id"))
        existing_test_ws = WSData.all_objects.filter(owner__isnull=True, region=test_region).count()
        if existing_test_ws == 0:
            clones = []
            for r in de_ws:
                clones.append(
                    WSData(
                        tag_im_jahr=r.tag_im_jahr,
                        solar_promille=r.solar_promille,
                        wind_promille=r.wind_promille,
                        heizung_abwaerm_promille=r.heizung_abwaerm_promille,
                        verbrauch_promille=r.verbrauch_promille,
                        region=test_region,
                    )
                )
            WSData.all_objects.bulk_create(clones, batch_size=1000)
            print(f"WSData: cloned {len(clones)}")
        else:
            print(f"WSData: skip (TEST already has {existing_test_ws} rows)")


if __name__ == "__main__":
    main()
