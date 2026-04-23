"""
Phase B (T65) — Region model schema + DE seed tests.

Verifies the Region table exists with required fields (SR-004 in
DATA_MODEL_IMPORT_AUDIT.md) and that a default DE row is seeded by
the Phase B migration with the installed-power constants that close
T54 D4a (194 GW, Pmax-Ely-ES) and D4b (261 GW, Pmax-Rückverstromung).
"""
from django.db import models as django_models
from django.test import TestCase


class RegionModelSchemaTests(TestCase):
    """Verifies Region model exists with the fields Phase B requires."""

    def test_region_model_importable(self):
        from simulator.models import Region

        self.assertEqual(Region._meta.app_label, "simulator")

    def test_region_has_code_field_unique(self):
        from simulator.models import Region

        field = Region._meta.get_field("code")
        self.assertIsInstance(field, django_models.CharField)
        self.assertTrue(field.unique, "Region.code must be unique")

    def test_region_has_display_name(self):
        from simulator.models import Region

        field = Region._meta.get_field("display_name")
        self.assertIsInstance(field, django_models.CharField)

    def test_region_has_active_bool(self):
        from simulator.models import Region

        field = Region._meta.get_field("active")
        self.assertIsInstance(field, django_models.BooleanField)
        self.assertTrue(field.default, "Region.active should default True")

    def test_region_has_datenmodell_excel_hash(self):
        """Per SR-004: hash of the source Datenmodell Excel for change detection."""
        from simulator.models import Region

        field = Region._meta.get_field("datenmodell_excel_hash")
        self.assertIsInstance(field, django_models.CharField)
        self.assertTrue(field.blank)

    def test_region_has_installed_pmax_ely_gw(self):
        """D4a region constant: Pmax of Elektrolyse-Stromspeicher (194 GW for DE)."""
        from simulator.models import Region

        field = Region._meta.get_field("installed_pmax_ely_gw")
        self.assertIsInstance(field, django_models.FloatField)

    def test_region_has_installed_pmax_rv_gw(self):
        """D4b region constant: Pmax of Rückverstromung (261 GW for DE)."""
        from simulator.models import Region

        field = Region._meta.get_field("installed_pmax_rv_gw")
        self.assertIsInstance(field, django_models.FloatField)

    def test_region_has_created_at(self):
        from simulator.models import Region

        field = Region._meta.get_field("created_at")
        self.assertIsInstance(field, django_models.DateTimeField)
        self.assertTrue(field.auto_now_add)


class RegionDefaultSeedTests(TestCase):
    """Verifies the DE row is seeded by the Phase B migration."""

    def test_DE_seed_row_present(self):
        from simulator.models import Region

        de = Region.objects.get(code="DE")
        self.assertEqual(de.display_name, "Deutschland")
        self.assertTrue(de.active)

    def test_DE_seed_has_installed_pmax_ely_194(self):
        """D4a: 194 GW (Pmax-Ely-ES) for Germany 2026 — sourced from D.xlsx I_Basisdaten."""
        from simulator.models import Region

        de = Region.objects.get(code="DE")
        self.assertEqual(de.installed_pmax_ely_gw, 194.0)

    def test_DE_seed_has_installed_pmax_rv_261(self):
        """D4b: 261 GW (Pmax-Rückverstromung) for Germany 2026."""
        from simulator.models import Region

        de = Region.objects.get(code="DE")
        self.assertEqual(de.installed_pmax_rv_gw, 261.0)

    def test_only_DE_in_phase_b_default(self):
        """Phase B ships single-region; only DE present in the default fixture."""
        from simulator.models import Region

        codes = list(Region.objects.values_list("code", flat=True).order_by("code"))
        self.assertEqual(codes, ["DE"])
