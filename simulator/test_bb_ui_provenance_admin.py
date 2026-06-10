from django.contrib.auth import get_user_model
from django.test import TestCase

from simulator.models import LandUse


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
