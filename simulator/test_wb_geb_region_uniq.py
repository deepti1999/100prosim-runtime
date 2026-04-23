"""
Phase C (T66) — GebaeudewaermeData uniqueness must include region so the
same code can coexist across regions when Bundesländer-data ships.

Phase B left a TODO note (`simulator/models.py:1537`) flagging that
GebaeudewaermeData.code stays globally unique=True for Phase B (DE-only).
This test asserts the (region, code) replacement landed.
"""
from django.db import IntegrityError
from django.test import TestCase


class GebaeudewaermeRegionUniqueConstraintTests(TestCase):
    def test_constraint_is_region_plus_code_not_just_code(self):
        from simulator.models import GebaeudewaermeData

        constraint_field_sets = [
            set(c.fields)
            for c in GebaeudewaermeData._meta.constraints
            if hasattr(c, "fields") and c.fields
        ]
        self.assertIn(
            {"region", "code"},
            constraint_field_sets,
            "GebaeudewaermeData must have UniqueConstraint(['region','code']) "
            "so per-Bundesland data using the same code (e.g. '2.1') can coexist.",
        )

    def test_code_field_is_no_longer_globally_unique(self):
        """Field-level unique=True is incompatible with multi-region code reuse."""
        from simulator.models import GebaeudewaermeData

        code_field = GebaeudewaermeData._meta.get_field("code")
        self.assertFalse(
            code_field.unique,
            "GebaeudewaermeData.code must drop unique=True; uniqueness now lives "
            "in the (region, code) constraint instead.",
        )

    def test_same_code_allowed_across_regions(self):
        from simulator.models import GebaeudewaermeData, Region

        de = Region.objects.get(code="DE")
        bb = Region.objects.create(code="BB", display_name="Brandenburg", active=True)

        GebaeudewaermeData.objects.create(
            code="2.99_TEST", category="DE building", unit="GWh/a", region=de
        )
        # Same code, different region — must NOT raise.
        GebaeudewaermeData.objects.create(
            code="2.99_TEST", category="BB building", unit="GWh/a", region=bb
        )

    def test_same_code_same_region_still_blocked(self):
        from simulator.models import GebaeudewaermeData, Region

        de = Region.objects.get(code="DE")
        GebaeudewaermeData.objects.create(
            code="2.98_DUP", category="first", unit="GWh/a", region=de
        )
        with self.assertRaises(IntegrityError):
            GebaeudewaermeData.objects.create(
                code="2.98_DUP", category="duplicate", unit="GWh/a", region=de
            )
