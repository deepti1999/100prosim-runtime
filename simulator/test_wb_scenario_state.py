"""White-box tests for internal scenario/session state behavior."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import ScenarioSnapshot, RenewableData

def _diagram_stub():
    return {
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

class WhiteBoxScenarioStateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="wb_scenario_user",
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

    def test_create_scenario_sets_active_session(self):
        response = self._post_json(
            reverse("simulator:create_scenario"),
            {"name": "Scenario Alpha", "note": "first"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        session = self.client.session
        self.assertEqual(session["active_scenario_scope"], f"user:{self.user.id}")
        self.assertEqual(session["active_scenario_name"], "Scenario Alpha")
        self.assertTrue(session["active_scenario_updated_at"])

    def test_create_scenario_rejects_duplicate_names_in_same_scope(self):
        ScenarioSnapshot.objects.create(owner=self.user, name="Scenario Alpha", payload={})

        response = self._post_json(
            reverse("simulator:create_scenario"),
            {"name": "scenario alpha"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("already exists", response.json()["error"])

    def test_rename_scenario_updates_active_session_name(self):
        scenario = ScenarioSnapshot.objects.create(owner=self.user, name="Old Name", payload={})
        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_id"] = scenario.id
        session["active_scenario_name"] = scenario.name
        session["active_scenario_updated_at"] = "11.03.2026 12:00"
        session.save()

        response = self._post_json(
            reverse("simulator:rename_scenario", kwargs={"scenario_id": scenario.id}),
            {"name": "New Name"},
        )

        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(session["active_scenario_name"], "New Name")

    def test_delete_active_scenario_clears_active_session(self):
        scenario = ScenarioSnapshot.objects.create(owner=self.user, name="To Delete", payload={})
        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_id"] = scenario.id
        session["active_scenario_name"] = scenario.name
        session["active_scenario_updated_at"] = "11.03.2026 12:00"
        session.save()

        response = self.client.post(
            reverse("simulator:delete_scenario", kwargs={"scenario_id": scenario.id})
        )

        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertNotIn("active_scenario_name", session)
        self.assertNotIn("active_scenario_scope", session)
        self.assertFalse(ScenarioSnapshot.objects.filter(id=scenario.id).exists())

    def test_restore_baseline_clears_active_session_for_current_scope(self):
        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_id"] = 7
        session["active_scenario_name"] = "Scenario Alpha"
        session["active_scenario_updated_at"] = "11.03.2026 12:00"
        session.save()

        with patch("simulator.baseline_api._restore_snapshot_payload"):
            with patch("simulator.baseline_api.BaselineSnapshot.objects.filter") as mock_filter:
                mock_filter.return_value.first.return_value = type("Snap", (), {"payload": {}})()
                response = self.client.post(reverse("simulator:restore_baseline"))

        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertNotIn("active_scenario_name", session)
        self.assertNotIn("active_scenario_scope", session)

    @patch("simulator.page_renewable.get_ws_365_data")
    @patch("simulator.page_renewable.get_ws_constants")
    @patch("simulator.page_renewable.compute_ws_diagram_reference")
    def test_annual_page_uses_active_scenario_session_fields(
        self,
        mock_diagram,
        mock_constants,
        mock_ws_data,
    ):
        mock_diagram.return_value = _diagram_stub()
        mock_constants.return_value = {"ETA_STROM_GAS": 0.65, "ETA_GAS_STROM": 0.585}
        mock_ws_data.return_value = {
            "current": {"storage_drift": 0.0, "ladezust_day1": 1.0, "ladezust_day365": 1.0},
            "daily_data": [{"day": 1, "ladezust_abs_vorl_tl": 12.0}],
        }
        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_name"] = "Scenario Alpha"
        session["active_scenario_updated_at"] = "11.03.2026 18:10"
        session.save()

        response = self.client.get(reverse("simulator:annual_electricity"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scenario Alpha")
        self.assertContains(response, "11.03.2026 18:10")
