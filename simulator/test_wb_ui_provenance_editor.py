from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from simulator.admin_roles import ensure_admin_role_groups
from simulator.models import LandUse, Region, UIProvenanceOverride


class UIProvenanceEditorViewTests(TestCase):
    def setUp(self):
        ensure_admin_role_groups()
        self.region = Region.objects.get(code="DE")
        self.row = LandUse.objects.create(
            code="LU_TEST",
            name="Testfläche",
            region=self.region,
            status_ha=100.0,
            target_ha=120.0,
            notes_assumption="- STATUS-Ansatz: Importierter Status.\n\n- ZIEL-Ansatz: Importiertes Ziel.",
            source_refs=[
                {
                    "section": "status",
                    "label": "Statusquelle",
                    "description": "Beschreibung Status",
                    "url": "https://example.com/status",
                }
            ],
        )
        self.url = reverse("simulator:ui_provenance_edit")
        self.User = get_user_model()

    def _user(self, username, role_name=None):
        user = self.User.objects.create_user(
            username=username,
            password="pass",
            is_staff=True,
        )
        if role_name:
            user.groups.add(Group.objects.get(name=role_name))
        return user

    def test_user_without_editor_permission_cannot_open_editor(self):
        viewer = self._user("viewer", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(
            self.url,
            {
                "domain": "landuse",
                "row_code": self.row.code,
                "region_id": self.region.pk,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_can_open_prefilled_editor(self):
        editor = self._user("editor", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.get(
            self.url,
            {
                "domain": "landuse",
                "row_code": self.row.code,
                "region_id": self.region.pk,
                "return_url": reverse("simulator:landuse_list"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quelleninformation bearbeiten")
        self.assertContains(response, "Importierter Status")
        self.assertContains(response, "Statusquelle")

    def test_editor_can_save_user_friendly_provenance_from_webapp_ui(self):
        editor = self._user("editor", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.post(
            self.url,
            {
                "domain": "landuse",
                "row_code": self.row.code,
                "region_id": self.region.pk,
                "return_url": reverse("simulator:landuse_list"),
                "is_active": "on",
                "general_information": "Allgemeine Erklärung aus der UI.",
                "status_information": "Status wurde direkt in der Webapp gepflegt.",
                "ziel_information": "Ziel wurde direkt in der Webapp gepflegt.",
                "sources-TOTAL_FORMS": "2",
                "sources-INITIAL_FORMS": "0",
                "sources-MIN_NUM_FORMS": "0",
                "sources-MAX_NUM_FORMS": "8",
                "sources-0-section": "status",
                "sources-0-label": "GENESIS",
                "sources-0-description": "Regionaldatenbank Deutschland",
                "sources-0-url": "https://example.com/genesis",
                "sources-0-sort_order": "0",
                "sources-1-section": "ziel",
                "sources-1-label": "",
                "sources-1-description": "",
                "sources-1-url": "",
                "sources-1-sort_order": "1",
            },
        )

        self.assertRedirects(response, reverse("simulator:landuse_list"))
        override = UIProvenanceOverride.objects.get(
            domain="landuse",
            row_code=self.row.code,
            region=self.region,
        )
        self.assertEqual(override.row_label, "Testfläche")
        self.assertEqual(override.status_information, "Status wurde direkt in der Webapp gepflegt.")
        self.assertEqual(override.sources.count(), 1)
        self.assertEqual(override.sources.first().label, "GENESIS")

    def test_landuse_page_shows_clear_edit_controls_only_to_permitted_editor(self):
        editor = self._user("editor_page", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quellen-Bearbeitung aktiv")
        self.assertContains(response, "Bearbeiten")
        self.assertContains(response, "quelleninfo/bearbeiten")

    def test_landuse_page_hides_edit_controls_from_viewer(self):
        viewer = self._user("viewer_page", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Quellen-Bearbeitung aktiv")
        self.assertNotContains(response, "quelleninfo/bearbeiten")
