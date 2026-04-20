"""Django-level end-to-end tests for current scenario and annual-flow behavior."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import RenewableData

class E2EScenarioFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="e2e_scenario_user",
            password="test-pass-123",
        )
        RenewableData.objects.create(
            owner=cls.user,
            code="9.4.1",
            name="Stromnetz zum Endverbrauch",
            category="renewable",
            unit="GWh",
            status_value=0.0,
            target_value=0.0,
            is_fixed=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    @patch("simulator.page_renewable.get_ws_365_data")
    @patch("simulator.page_renewable.get_ws_constants")
    @patch("simulator.page_renewable.compute_ws_diagram_reference")
    def test_saved_renamed_deleted_scenario_changes_annual_header_end_to_end(
        self,
        mock_diagram,
        mock_constants,
        mock_ws_data,
    ):
        mock_diagram.return_value = {
            "pv_value": 10.0,
            "wind_value": 20.0,
            "bio_value": 5.0,
            "hydro_value": 2.0,
            "m_total": 37.0,
            "ely_branch_value": 3.0,
            "n_value": 30.0,
            "n_input_branch": 4.0,
            "n_output_branch": 2.5,
            "gas_storage": 2.5,
            "storage_capacity": 12.0,
            "t_value": 2.5,
            "t_output": 1.5,
            "n_to_right": 18.0,
            "final_stromnetz": 42.0,
            "h2_offer": 2.5,
            "h2_surplus": 2.5,
            "q_abregelung": 1.0,
            "solarstrom_366": 10.0,
            "windstrom_366": 20.0,
            "sonst_kraft_konstant_366": 1.0,
        }
        mock_constants.return_value = {"ETA_STROM_GAS": 0.65, "ETA_GAS_STROM": 0.585}
        mock_ws_data.return_value = {
            "current": {"storage_drift": 0.0, "ladezust_day1": 1.0, "ladezust_day365": 1.0},
            "daily_data": [{"day": 1, "ladezust_abs_vorl_tl": 12.0}],
        }

        create_response = self._post_json(
            reverse("simulator:create_scenario"),
            {"name": "Scenario One"},
        )
        self.assertEqual(create_response.status_code, 200)
        scenario_id = create_response.json()["id"]

        annual_after_create = self.client.get(reverse("simulator:annual_electricity"))
        self.assertContains(annual_after_create, "Scenario One")

        rename_response = self._post_json(
            reverse("simulator:rename_scenario", kwargs={"scenario_id": scenario_id}),
            {"name": "Scenario Two"},
        )
        self.assertEqual(rename_response.status_code, 200)

        annual_after_rename = self.client.get(reverse("simulator:annual_electricity"))
        self.assertContains(annual_after_rename, "Scenario Two")

        delete_response = self.client.post(
            reverse("simulator:delete_scenario", kwargs={"scenario_id": scenario_id})
        )
        self.assertEqual(delete_response.status_code, 200)

        annual_after_delete = self.client.get(reverse("simulator:annual_electricity"))
        self.assertContains(annual_after_delete, "Aktuelles Szenario")
