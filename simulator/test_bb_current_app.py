"""Black-box tests for the current user-visible web app behavior."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import RenewableData

def _annual_diagram_stub():
    return {
        "pv_value": 1200.0,
        "wind_value": 700.0,
        "bio_value": 100.0,
        "hydro_value": 50.0,
        "m_total": 2050.0,
        "ely_branch_value": 385.0,
        "n_value": 1541.0,
        "n_input_branch": 405.0,
        "n_output_branch": 263.0,
        "gas_storage": 260.0,
        "storage_capacity": 241.7,
        "t_value": 263.0,
        "t_output": 153.9,
        "n_to_right": 947.0,
        "final_stromnetz": 1105.5,
        "h2_offer": 263.0,
        "h2_surplus": 263.0,
        "q_abregelung": 189.1,
        "solarstrom_366": 1200.0,
        "windstrom_366": 700.0,
        "sonst_kraft_konstant_366": 55.0,
    }

def _ws_constants_stub():
    return {
        "ETA_STROM_GAS": 0.65,
        "ETA_GAS_STROM": 0.585,
    }

def _ws_daily_stub():
    return {
        "current": {
            "storage_drift": 0.0,
            "ladezust_day1": 100.0,
            "ladezust_day365": 100.0,
        },
        "daily_data": [
            {
                "day": 1,
                "solar_promille": 1.0,
                "wind_promille": 1.0,
                "heizung_abwaerm_promille": 1.0,
                "verbrauch_promille": 1.0,
                "ladezust_abs_vorl_tl": 241.7,
                "ladezust_brutto": 100.0,
                "ladezust_netto": 100.0,
                "ladezust_absolute": 100.0,
            }
        ],
    }

class BlackBoxCurrentAppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="bb_current_user",
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

    def test_dashboard_shows_current_cards_and_quick_links(self):
        response = self.client.get(reverse("simulator:main_simulation"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Simulations-Übersicht")
        self.assertContains(response, "Flächennutzung")
        self.assertContains(response, "Erneuerbare Energien")
        self.assertContains(response, "Verbrauch")
        self.assertContains(response, "Szenario-Abgleich")
        self.assertContains(response, "Steuerungs-Cockpit")
        self.assertContains(response, "Jahresstrom")
        self.assertContains(response, "Bilanz")
        self.assertContains(response, "Benutzerhandbuch")

    def test_sidebar_labels_match_current_webapp(self):
        response = self.client.get(reverse("simulator:main_simulation"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Übersicht")
        self.assertContains(response, "Flächennutzung")
        self.assertContains(response, "Erneuerbare Energien")
        self.assertContains(response, "Verbrauch")
        self.assertContains(response, "Szenario-Abgleich")
        self.assertContains(response, "Cockpit")
        self.assertContains(response, "Jahresstrom")
        self.assertContains(response, "Bilanz")
        self.assertContains(response, "Benutzerhandbuch")
        self.assertNotContains(response, "WS (365 Tage)")
        self.assertNotContains(response, "Verbrauch (KLIK + Gebäudewärme)")

    @patch("simulator.ws_api._build_ws_summary_context")
    def test_ws_page_shows_current_controls_and_annual_flow_link(self, mock_summary):
        mock_summary.return_value = {
            "current": {"annual_electricity": 1000.0},
            "goal_seek": {},
            "goal_seek_wind": {},
            "daily_data": [],
            "optimal_daily_data": [],
        }

        response = self.client.get(reverse("simulator:ws"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Szenario-Abgleich")
        self.assertContains(response, "WS Balance Solar")
        self.assertContains(response, "Sector + WS Solar Balance")
        self.assertContains(response, "WS Balance Wind")
        self.assertContains(response, "Sector + WS Wind Balance")
        self.assertContains(response, "Jahresstrom-Hinweis")
        self.assertContains(response, "Zur Seite Jahresstrom")
        # Stakeholder T19/T20 (PDF §2.4.3): "Goal Seek" and "Aktualisieren"
        # buttons removed — goal-seek runs automatically on page load.
        self.assertNotContains(response, 'id="runGoalSeekBtn"')
        self.assertNotContains(response, 'id="refreshDataBtn"')

    @patch("simulator.page_renewable.get_ws_365_data")
    @patch("simulator.page_renewable.get_ws_constants")
    @patch("simulator.page_renewable.compute_ws_diagram_reference")
    def test_annual_electricity_page_shows_default_current_scenario_header(
        self,
        mock_diagram,
        mock_constants,
        mock_ws_data,
    ):
        mock_diagram.return_value = _annual_diagram_stub()
        mock_constants.return_value = _ws_constants_stub()
        mock_ws_data.return_value = _ws_daily_stub()

        response = self.client.get(reverse("simulator:annual_electricity"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jahresbilanz Strom")
        self.assertContains(response, "Aktuelles Szenario")
        self.assertContains(response, "Stand")

    @patch("simulator.page_renewable.get_ws_365_data")
    @patch("simulator.page_renewable.get_ws_constants")
    @patch("simulator.page_renewable.compute_ws_diagram_reference")
    def test_annual_electricity_page_shows_active_scenario_header_when_session_is_set(
        self,
        mock_diagram,
        mock_constants,
        mock_ws_data,
    ):
        mock_diagram.return_value = _annual_diagram_stub()
        mock_constants.return_value = _ws_constants_stub()
        mock_ws_data.return_value = _ws_daily_stub()

        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_name"] = "Wind Test v1"
        session["active_scenario_updated_at"] = "11.03.2026 14:45"
        session.save()

        response = self.client.get(reverse("simulator:annual_electricity"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jahresbilanz Strom")
        self.assertContains(response, "Wind Test v1")
        self.assertContains(response, "11.03.2026 14:45")

    def test_user_manual_page_loads(self):
        response = self.client.get(reverse("simulator:user_manual"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User Manual")
