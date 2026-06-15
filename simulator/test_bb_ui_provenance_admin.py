from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse, UIProvenanceOverride, UIProvenanceSource


class UIProvenanceAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="ui_prov_admin",
            password="x",
            is_staff=True,
            is_superuser=True,
        )
        cls.row = LandUse.objects.create(
            code="LU_1.1",
            name="Solare Dachflächen",
            status_ha=34243.0,
            target_ha=199398.0,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_add_override_form_prefills_from_querystring_and_shows_plain_labels(self):
        response = self.client.get(
            "/admin/simulator/uiprovenanceoverride/add/",
            {
                "domain": "landuse",
                "row_code": "LU_1.1",
                "row_label": "Solare Dachflächen",
                "region": self.row.region_id,
            },
            HTTP_HOST="localhost:8002",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zeilen-Code")
        self.assertContains(response, "Status-Erklärung")
        self.assertContains(response, "Ziel-Erklärung")
        self.assertContains(response, 'value="LU_1.1"')
        self.assertContains(response, 'value="Solare Dachflächen"')


class UIProvenanceDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="ui_prov_user", password="x")
        cls.row = LandUse.objects.create(
            code="LU_1.1",
            name="Solare Dachflächen",
            status_ha=34243.0,
            target_ha=199398.0,
            notes_assumption="Legacy note hidden by override",
        )
        cls.override = UIProvenanceOverride.objects.create(
            region=cls.row.region,
            domain="landuse",
            row_code="LU_1.1",
            row_label="Solare Dachflächen",
            general_information="Allgemeine Einordnung.",
            status_information="Status kommt aus dem Bestand.",
            ziel_information="Ziel kommt aus der Potenzialstudie.",
        )
        UIProvenanceSource.objects.create(
            override=cls.override,
            section="status",
            label="Statusquelle",
            description="Status-Beschreibung",
            url="https://example.com/status",
        )
        UIProvenanceSource.objects.create(
            override=cls.override,
            section="ziel",
            label="Zielquelle",
            description="Ziel-Beschreibung",
            url="https://example.com/ziel",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_data_source_detail_shows_only_selected_row_status_and_ziel_sources(self):
        response = self.client.get(
            reverse("simulator:data_source_detail", args=["landuse", "LU_1.1"]),
            {"region_id": self.row.region_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datenquelle im Detail")
        self.assertContains(response, "LU_1.1")
        self.assertContains(response, "Solare Dachflächen")
        self.assertContains(response, "Status kommt aus dem Bestand.")
        self.assertContains(response, "Ziel kommt aus der Potenzialstudie.")
        self.assertContains(response, "Statusquelle")
        self.assertContains(response, "Zielquelle")

    def test_code_popover_links_to_full_detail_page(self):
        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Details anzeigen")
        self.assertContains(response, reverse("simulator:data_source_detail", args=["landuse", "LU_1.1"]))
