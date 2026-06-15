from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.admin_versioning import clone_region_data_model, region_data_model_counts
from simulator.workspace_service import sync_all_templates_to_user_rows
from simulator.models import (
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    UIProvenanceOverride,
    UIProvenanceSource,
    VerbrauchData,
)
from simulator.ws_models import WSData


class RegionDataModelCloneTests(TestCase):
    def setUp(self):
        self.source, _ = Region.objects.get_or_create(
            code="DE",
            defaults={"display_name": "Deutschland", "total_area_ha": 35759529},
        )
        self.target = Region.objects.create(
            code="FR",
            display_name="Frankreich",
            total_area_ha=54394000,
        )
        self.user = get_user_model().objects.create_user(
            username="workspace-sync-user",
            password="pass",
        )
        self.root = LandUse.all_objects.create(
            region=self.source,
            owner=None,
            code="LU_CLONE_ROOT",
            name="Root",
            status_ha=10,
            target_ha=20,
        )
        LandUse.all_objects.create(
            region=self.source,
            owner=None,
            parent=self.root,
            code="LU_CLONE_CHILD",
            name="Child",
            status_ha=3,
            target_ha=4,
            origin="d_xlsx",
            source_refs=[{"label": "Quelle"}],
        )
        RenewableData.all_objects.create(
            region=self.source,
            owner=None,
            category="Test",
            code="RE_CLONE",
            name="Renewable",
            unit="GWh/a",
            status_value=1,
            target_value=2,
        )
        VerbrauchData.all_objects.create(
            region=self.source,
            owner=None,
            code="V_CLONE",
            category="Verbrauch",
            unit="GWh/a",
            status=5,
            ziel=6,
        )
        GebaeudewaermeData.all_objects.create(
            region=self.source,
            code="GW_CLONE",
            category="Gebaeudewärme",
            unit="GWh/a",
            status=7,
            ziel=8,
        )
        WSData.all_objects.create(
            region=self.source,
            owner=None,
            tag_im_jahr=1,
            solar_promille=11,
            wind_promille=12,
        )
        override = UIProvenanceOverride.objects.create(
            region=self.source,
            domain="landuse",
            row_code="LU_CLONE_CHILD",
            row_label="Child",
            status_information="Status text",
            ziel_information="Ziel text",
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="status",
            label="Source",
            description="Source description",
            url="https://example.com",
        )

    def test_clone_copies_region_rows_without_changing_source(self):
        counts = clone_region_data_model(self.source, self.target)

        self.assertEqual(counts["landuse"], 2)
        self.assertEqual(counts["renewable"], 1)
        self.assertEqual(counts["verbrauch"], 1)
        self.assertEqual(counts["gebaeudewaerme"], 1)
        self.assertEqual(counts["ws"], 1)
        self.assertEqual(counts["ui_provenance"], 1)

        source_child = LandUse.all_objects.get(region=self.source, code="LU_CLONE_CHILD")
        target_child = LandUse.all_objects.get(region=self.target, code="LU_CLONE_CHILD")
        self.assertNotEqual(source_child.pk, target_child.pk)
        self.assertEqual(target_child.status_ha, 3)
        self.assertEqual(target_child.parent.code, "LU_CLONE_ROOT")
        self.assertEqual(source_child.region.code, "DE")

        target_override = UIProvenanceOverride.objects.get(
            region=self.target,
            domain="landuse",
            row_code="LU_CLONE_CHILD",
        )
        self.assertEqual(target_override.status_information, "Status text")
        self.assertEqual(target_override.sources.get().label, "Source")

    def test_region_data_model_counts_are_region_specific(self):
        clone_region_data_model(self.source, self.target)

        source_counts = region_data_model_counts(self.source)
        target_counts = region_data_model_counts(self.target)

        self.assertEqual(source_counts["landuse"], 2)
        self.assertEqual(target_counts["landuse"], 2)
        self.assertEqual(target_counts["ws"], 1)

    def test_admin_template_edits_sync_to_existing_user_workspace_rows(self):
        user_root = LandUse.all_objects.create(
            region=self.source,
            owner=self.user,
            code=self.root.code,
            name="Old user root",
            status_ha=1,
            target_ha=2,
        )
        renewable = RenewableData.all_objects.get(region=self.source, code="RE_CLONE")
        user_renewable = RenewableData.all_objects.create(
            region=self.source,
            owner=self.user,
            category="Old",
            code=renewable.code,
            name="Old renewable",
            unit="old",
            status_value=1,
            target_value=2,
        )
        verbrauch = VerbrauchData.all_objects.get(region=self.source, code="V_CLONE")
        user_verbrauch = VerbrauchData.all_objects.create(
            region=self.source,
            owner=self.user,
            code=verbrauch.code,
            category="Old Verbrauch",
            unit="old",
            status=1,
            ziel=2,
        )
        ws = WSData.all_objects.get(region=self.source, owner=None, tag_im_jahr=1)
        user_ws = WSData.all_objects.create(
            region=self.source,
            owner=self.user,
            tag_im_jahr=ws.tag_im_jahr,
            solar_promille=1,
            wind_promille=2,
        )

        self.root.name = "Updated root"
        self.root.status_ha = 100
        self.root.target_ha = 200
        renewable.name = "Updated renewable"
        renewable.status_value = 300
        renewable.target_value = 400
        verbrauch.category = "Updated Verbrauch"
        verbrauch.status = 500
        verbrauch.ziel = 600
        ws.solar_promille = 700
        ws.wind_promille = 800

        with self.captureOnCommitCallbacks(execute=True):
            self.root.save()
            renewable.save(skip_cascade=True)
            verbrauch.save(skip_cascade=True)
            ws.save()

        user_root.refresh_from_db()
        user_renewable.refresh_from_db()
        user_verbrauch.refresh_from_db()
        user_ws.refresh_from_db()

        self.assertEqual(user_root.name, "Updated root")
        self.assertEqual(user_root.status_ha, 100)
        self.assertEqual(user_root.target_ha, 200)
        self.assertEqual(user_renewable.name, "Updated renewable")
        self.assertEqual(user_renewable.status_value, 300)
        self.assertEqual(user_renewable.target_value, 400)
        self.assertEqual(user_verbrauch.category, "Updated Verbrauch")
        self.assertEqual(user_verbrauch.status, 500)
        self.assertEqual(user_verbrauch.ziel, 600)
        self.assertEqual(user_ws.solar_promille, 700)
        self.assertEqual(user_ws.wind_promille, 800)

    def test_one_time_template_sync_repairs_existing_user_rows(self):
        user_root = LandUse.all_objects.create(
            region=self.source,
            owner=self.user,
            code=self.root.code,
            name="Stale root",
            status_ha=1,
            target_ha=2,
        )

        self.root.name = "Current admin root"
        self.root.status_ha = 123
        self.root.target_ha = 456
        self.root.save(skip_cascade=True)

        updated = sync_all_templates_to_user_rows(region_code=self.source.code)

        user_root.refresh_from_db()
        self.assertGreaterEqual(updated, 1)
        self.assertEqual(user_root.name, "Current admin root")
        self.assertEqual(user_root.status_ha, 123)
        self.assertEqual(user_root.target_ha, 456)


class RegionDataModelCloneAdminTests(TestCase):
    def setUp(self):
        self.source, _ = Region.objects.get_or_create(
            code="DE",
            defaults={"display_name": "Deutschland", "total_area_ha": 35759529},
        )
        LandUse.all_objects.create(
            region=self.source,
            owner=None,
            code="LU_ADMIN_CLONE",
            name="Admin clone row",
            status_ha=10,
            target_ha=20,
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin-clone",
            email="admin@example.com",
            password="pass",
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_create_new_region_from_existing_data_model(self):
        response = self.client.post(
            reverse("admin:simulator_region_copy_data_model"),
            {
                "source_region": self.source.pk,
                "code": "AT",
                "display_name": "Österreich",
                "locale_code": "de-AT",
                "status_year": 2023,
                "target_year": 2045,
                "goal_description": "100 % Erneuerbare Energien",
                "total_area_ha": 8387900,
                "data_source_label": "Testdaten",
                "active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        target = Region.objects.get(code="AT")
        self.assertEqual(target.display_name, "Österreich")
        self.assertTrue(
            LandUse.all_objects.filter(
                region=target,
                owner=None,
                code="LU_ADMIN_CLONE",
                status_ha=10,
            ).exists()
        )
        self.assertTrue(
            LandUse.all_objects.filter(
                region=self.source,
                owner=None,
                code="LU_ADMIN_CLONE",
                status_ha=10,
            ).exists()
        )
