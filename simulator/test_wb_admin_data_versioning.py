from django.test import TestCase

from simulator.admin_versioning import capture_admin_version_payload, restore_admin_version_payload
from simulator.models import (
    Formula,
    FormulaVariable,
    LandUse,
    Region,
    UIProvenanceOverride,
    UIProvenanceSource,
)


class AdminDataVersioningTests(TestCase):
    def setUp(self):
        self.region, _ = Region.objects.get_or_create(
            code="DE",
            defaults={"display_name": "Deutschland"},
        )

    def test_capture_and_restore_global_admin_state(self):
        landuse = LandUse.all_objects.create(
            region=self.region,
            owner=None,
            code="LU_TEST",
            name="Testfläche",
            status_ha=10,
            target_ha=20,
            user_percent=30,
            origin="d_xlsx",
            source_refs=[{"label": "Quelle A"}],
        )
        formula = Formula.objects.create(
            key="TEST_FORMULA",
            expression="1 + 2",
            category="landuse",
            formula_type="status",
            is_active=True,
        )
        FormulaVariable.objects.create(
            formula=formula,
            variable_name="x",
            source_type=FormulaVariable.LITERAL,
            source_key="1",
        )
        override = UIProvenanceOverride.objects.create(
            region=self.region,
            domain="landuse",
            row_code="LU_TEST",
            row_label="Testfläche",
            status_information="Original status text",
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="status",
            label="Original source",
            description="Original source description",
            url="https://example.com/source",
        )

        payload = capture_admin_version_payload("DE")

        landuse.status_ha = 999
        landuse.save(skip_cascade=True)
        formula.expression = "999"
        formula.save()
        override.status_information = "Changed text"
        override.save()

        restored = restore_admin_version_payload(payload)

        restored_landuse = LandUse.all_objects.get(region=self.region, owner=None, code="LU_TEST")
        restored_formula = Formula.objects.get(key="TEST_FORMULA")
        restored_override = UIProvenanceOverride.objects.get(
            region=self.region,
            domain="landuse",
            row_code="LU_TEST",
        )

        self.assertGreaterEqual(restored["landuse"], 1)
        self.assertEqual(restored_landuse.status_ha, 10)
        self.assertEqual(restored_landuse.target_ha, 20)
        self.assertEqual(restored_formula.expression, "1 + 2")
        self.assertEqual(restored_override.status_information, "Original status text")
        self.assertEqual(restored_override.sources.get().label, "Original source")
