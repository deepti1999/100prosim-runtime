"""
Phase B (T65) — region FK presence + default-DE tests on the 4
parameter models.

Verifies:
- LandUse / RenewableData / VerbrauchData / GebaeudewaermeData each
  have a `region` ForeignKey to Region with on_delete=PROTECT.
- A row created without an explicit region defaults to DE (so the
  Phase B migration backfill on existing rows + the workspace clone
  helpers all land at region=DE without per-call plumbing).
- Owner-scoped unique constraints (LandUse / RenewableData /
  VerbrauchData) include region so the same code can coexist across
  regions when Bundesländer-data ships.
- The `region` reverse accessor doesn't clash with the existing
  `owner` accessor (which already claims the simple `*_rows` name).
"""
from django.contrib.auth import get_user_model
from django.db import models as django_models
from django.test import TestCase


class RegionFKPresenceTests(TestCase):
    """Each parameter model has a region FK pointing at Region (PROTECT)."""

    def _assert_region_fk(self, model):
        from simulator.models import Region

        field = model._meta.get_field("region")
        self.assertIsInstance(field, django_models.ForeignKey)
        self.assertIs(field.related_model, Region)
        self.assertIs(
            field.remote_field.on_delete,
            django_models.PROTECT,
            f"{model.__name__}.region must use on_delete=PROTECT to "
            f"prevent accidental cascade-delete of all rows when a "
            f"Region is removed.",
        )

    def test_landuse_has_region_fk_protect(self):
        from simulator.models import LandUse

        self._assert_region_fk(LandUse)

    def test_renewable_has_region_fk_protect(self):
        from simulator.models import RenewableData

        self._assert_region_fk(RenewableData)

    def test_verbrauch_has_region_fk_protect(self):
        from simulator.models import VerbrauchData

        self._assert_region_fk(VerbrauchData)

    def test_gebaeudewaerme_has_region_fk_protect(self):
        from simulator.models import GebaeudewaermeData

        self._assert_region_fk(GebaeudewaermeData)


class RegionFKDefaultDETests(TestCase):
    """A row created without an explicit region picks up DE."""

    def test_landuse_default_DE(self):
        from simulator.models import LandUse

        row = LandUse.all_objects.create(code="ZZ_TEST_LU", name="phase-b probe")
        self.assertEqual(row.region.code, "DE")

    def test_renewable_default_DE(self):
        from simulator.models import RenewableData

        row = RenewableData.all_objects.create(
            category="ZZTest", name="phase-b probe", unit="GWh", code="ZZTEST_R"
        )
        self.assertEqual(row.region.code, "DE")

    def test_verbrauch_default_DE(self):
        from simulator.models import VerbrauchData

        row = VerbrauchData.all_objects.create(
            code="ZZ_TEST_V", category="phase-b probe", unit="GWh"
        )
        self.assertEqual(row.region.code, "DE")

    def test_gebaeudewaerme_default_DE(self):
        from simulator.models import GebaeudewaermeData

        row = GebaeudewaermeData.objects.create(
            code="ZZ_TEST_G", category="phase-b probe", unit="GWh"
        )
        self.assertEqual(row.region.code, "DE")


class RegionFKConstraintsTests(TestCase):
    """Owner-scoped uniqueness includes region so cross-region codes are allowed."""

    def _constraint_fields(self, model):
        result = []
        for c in model._meta.constraints:
            fields = getattr(c, "fields", None)
            if fields:
                result.append(set(fields))
        return result

    def test_landuse_owner_region_code_constraint(self):
        from simulator.models import LandUse

        constraint_field_sets = self._constraint_fields(LandUse)
        self.assertIn(
            {"owner", "region", "code"},
            constraint_field_sets,
            "LandUse needs UniqueConstraint(['owner','region','code']) so "
            "the same code can repeat across regions per workspace.",
        )

    def test_verbrauch_owner_region_code_constraint(self):
        from simulator.models import VerbrauchData

        self.assertIn(
            {"owner", "region", "code"},
            self._constraint_fields(VerbrauchData),
        )

    def test_renewable_owner_region_code_constraint(self):
        from simulator.models import RenewableData

        self.assertIn(
            {"owner", "region", "code"},
            self._constraint_fields(RenewableData),
        )


class RegionFKReverseAccessorNoClashTests(TestCase):
    """`region` FK uses a non-clashing reverse accessor — owner already owns *_rows."""

    def test_landuse_region_no_reverse_clash(self):
        from simulator.models import LandUse, Region

        # Just verifying we can spin up + describe both relations without
        # Django raising a "fields.E304" reverse-accessor clash check error.
        owner_relation = LandUse._meta.get_field("owner")
        region_relation = LandUse._meta.get_field("region")
        self.assertNotEqual(
            owner_relation.remote_field.get_accessor_name(),
            region_relation.remote_field.get_accessor_name(),
        )


class RegionFKBulkCloneDETests(TestCase):
    """Phase B step-2 backfill smoke: bulk_create with no region picks up DE.

    This exercises the same code path that workspace_service uses to clone
    base rows for a fresh user, ensuring the backfill on the live DB
    (migration RunPython) and the workspace clone helpers all converge to
    region=DE without per-call plumbing.
    """

    def test_bulk_create_landuse_defaults_DE(self):
        from simulator.models import LandUse, Region

        de_pk = Region.objects.get(code="DE").pk
        rows = [
            LandUse(code=f"ZZ_BULK_{i}", name=f"bulk probe {i}") for i in range(5)
        ]
        LandUse.all_objects.bulk_create(rows, batch_size=10)
        for created in LandUse.all_objects.filter(code__startswith="ZZ_BULK_"):
            self.assertEqual(created.region_id, de_pk)

    def test_bulk_create_renewable_defaults_DE(self):
        from simulator.models import RenewableData, Region

        de_pk = Region.objects.get(code="DE").pk
        rows = [
            RenewableData(
                category="ZZTest",
                name=f"bulk probe {i}",
                unit="GWh",
                code=f"ZZ_BULK_R_{i}",
            )
            for i in range(5)
        ]
        RenewableData.all_objects.bulk_create(rows, batch_size=10)
        for created in RenewableData.all_objects.filter(code__startswith="ZZ_BULK_R_"):
            self.assertEqual(created.region_id, de_pk)
