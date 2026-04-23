"""White-box tests for Phase A provenance schema.

Each parameter-bearing model (LandUse, RenewableData, VerbrauchData,
GebaeudewaermeData) must gain three additive provenance columns per
DATA_MODEL_IMPORT_AUDIT.md §9 D1:

  - source_url       URL to the D.xlsx 9.Quellen citation
  - notes_assumption Assumption text from D.xlsx 1. cell comments
  - origin           Enum {'d_xlsx', 'derived', 'internal'}, default 'internal'

These fields MUST be additive (nullable / default-set) so existing
seed rows stay unaffected and SR-005 (per-user overrides) holds.
"""

from django.test import TestCase
from django.db import connection

from simulator.models import (
    LandUse,
    RenewableData,
    VerbrauchData,
    GebaeudewaermeData,
)


PARAM_MODELS = [LandUse, RenewableData, VerbrauchData, GebaeudewaermeData]
NEW_FIELDS = ("source_url", "notes_assumption", "origin")
ORIGIN_CHOICES = {"d_xlsx", "derived", "internal"}


class TestProvenanceSchemaFields(TestCase):
    """SR-002 / SR-003 / SR-010: every parameter-bearing model carries provenance fields."""

    def test_every_model_has_source_url_field(self):
        for model in PARAM_MODELS:
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("source_url")
                self.assertTrue(field.null, f"{model.__name__}.source_url must be nullable")
                self.assertTrue(field.blank, f"{model.__name__}.source_url must allow blank")

    def test_every_model_has_notes_assumption_field(self):
        for model in PARAM_MODELS:
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("notes_assumption")
                self.assertTrue(field.null, f"{model.__name__}.notes_assumption must be nullable")
                self.assertTrue(field.blank, f"{model.__name__}.notes_assumption must allow blank")

    def test_every_model_has_origin_field_with_choices(self):
        for model in PARAM_MODELS:
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("origin")
                self.assertEqual(field.default, "internal", f"{model.__name__}.origin must default to 'internal'")
                choice_codes = {c[0] for c in field.choices}
                self.assertEqual(
                    choice_codes,
                    ORIGIN_CHOICES,
                    f"{model.__name__}.origin choices must be {ORIGIN_CHOICES}, got {choice_codes}",
                )


class TestProvenanceFieldsAreAdditiveOnly(TestCase):
    """SR-007 + SR-008: existing fields keep their semantics; new fields don't break create/save."""

    def test_landuse_existing_quelle_field_unchanged(self):
        """quelle is the existing LandUse 'Quelle' field (D.<sheet>.<paragraph> codes).
        It MUST keep its current shape — adding source_url is additive, not a rename."""
        field = LandUse._meta.get_field("quelle")
        self.assertEqual(field.max_length, 100)
        self.assertTrue(field.null)

    def test_renewabledata_existing_source_field_unchanged(self):
        """source is the existing RenewableData 'data source reference' field.
        Phase A must NOT repurpose it; it stays the per-row CSV identifier ('solar_energy.csv' etc.)."""
        field = RenewableData._meta.get_field("source")
        self.assertEqual(field.max_length, 100)

    def test_renewabledata_existing_notes_field_unchanged(self):
        """notes is the existing RenewableData 'additional notes' field.
        Phase A's new notes_assumption is separate; existing notes stays untouched."""
        field = RenewableData._meta.get_field("notes")
        self.assertTrue(field.null)

    def test_can_create_landuse_with_new_provenance_fields(self):
        row = LandUse.objects.create(
            code="TEST_LU_PROV",
            name="Test LandUse provenance",
            status_ha=1.0,
            target_ha=1.0,
            source_url="https://example.com/source.pdf",
            notes_assumption="Assumption text under test",
            origin="d_xlsx",
        )
        self.assertEqual(row.source_url, "https://example.com/source.pdf")
        self.assertEqual(row.notes_assumption, "Assumption text under test")
        self.assertEqual(row.origin, "d_xlsx")

    def test_can_create_renewabledata_with_new_provenance_fields(self):
        row = RenewableData.objects.create(
            code="TEST_REN_PROV",
            category="TestCat",
            unit="-",
            source_url="https://example.com/r.pdf",
            notes_assumption="r-notes",
            origin="derived",
        )
        self.assertEqual(row.origin, "derived")

    def test_can_create_verbrauchdata_with_new_provenance_fields(self):
        row = VerbrauchData.objects.create(
            code="TEST_VB_PROV",
            category="TestVB",
            unit="GWh/a",
            source_url="https://example.com/v.pdf",
            notes_assumption="v-notes",
            origin="internal",
        )
        self.assertEqual(row.origin, "internal")

    def test_can_create_gebaeudewaermedata_with_new_provenance_fields(self):
        row = GebaeudewaermeData.objects.create(
            code="TEST_GW_PROV",
            category="TestGW",
            unit="GWh/a",
            source_url="https://example.com/g.pdf",
            notes_assumption="g-notes",
            origin="d_xlsx",
        )
        self.assertEqual(row.origin, "d_xlsx")

    def test_existing_seed_rows_default_to_origin_internal(self):
        """SR-008: existing 420 seed rows MUST work without explicit origin."""
        # Just create a row without origin, confirm it defaults
        row = LandUse.objects.create(code="TEST_LU_DEFAULT", name="Default check", status_ha=1.0)
        self.assertEqual(row.origin, "internal", "Origin must default to 'internal' so existing rows are correctly classified")
