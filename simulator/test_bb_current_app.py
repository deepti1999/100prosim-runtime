"""Black-box tests for the current user-visible web app behavior."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse, RenewableData, UIProvenanceOverride, UIProvenanceSource

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
        LandUse.objects.create(
            code="LU_0",
            name="Bodenfläche gesamt",
            status_ha=35759529.0,
            target_ha=35759529.0,
            quelle="D.1.64",
            source_url="https://example.com/quelle",
            notes_assumption="Gemäß GENESIS basiert der Ausgangswert auf der amtlichen Flächenstatistik.",
            source_refs=[
                {
                    "code": "9.224",
                    "description": 'STATISTISCHE ÄMTER DES BUNDES UND DER LÄNDER: "Regionaldatenbank Deutschland"; Online-Angebot GENESIS.',
                    "url": "https://example.com/quelle",
                }
            ],
            origin="d_xlsx",
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

    def test_landuse_page_shows_excel_reference_code_and_provenance_details(self):
        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gemäß GENESIS basiert der Ausgangswert")
        self.assertContains(response, "Regionaldatenbank Deutschland")
        self.assertContains(response, "Quelle öffnen")
        self.assertNotContains(response, "GENESIS [9.224]")
        self.assertNotContains(response, "[D.1.64]")
        self.assertNotContains(response, "d_xlsx")

    def test_landuse_page_prefers_ui_provenance_override_when_present(self):
        row = LandUse.objects.get(code="LU_0")
        override = UIProvenanceOverride.objects.create(
            domain="landuse",
            row_code=row.code,
            row_label=row.name,
            region=row.region,
            general_information="Klarer Admin-Text fuer die UI.",
            status_information="Dieser Wert wurde manuell fuer die Benutzeransicht erklaert.",
            ziel_information="Das Ziel bleibt hier identisch zum Status.",
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="status",
            label="Amtliche Statistik",
            description="Benutzerfreundliche Quellenbeschreibung aus dem Admin.",
            url="https://example.com/admin-source",
            sort_order=1,
        )

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Klarer Admin-Text fuer die UI.")
        self.assertContains(response, "Benutzerfreundliche Quellenbeschreibung aus dem Admin.")
        self.assertContains(response, "https://example.com/admin-source")
        self.assertNotContains(response, "Gemäß GENESIS basiert der Ausgangswert")

    def test_landuse_page_shows_override_text_exactly_as_written(self):
        row = LandUse.objects.get(code="LU_0")
        override = UIProvenanceOverride.objects.create(
            domain="landuse",
            row_code=row.code,
            row_label=row.name,
            region=row.region,
            status_information="Admin-Text mit [9.224] bleibt exakt so stehen.",
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="status",
            label="Adminquelle",
            description="Quelle aus dem Admin.",
            url="https://example.com/admin-source-exact",
            sort_order=1,
        )

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin-Text mit [9.224] bleibt exakt so stehen.")
        self.assertNotContains(response, "Gemäß GENESIS basiert der Ausgangswert")

    def test_landuse_page_empty_active_override_suppresses_fallback_provenance(self):
        row = LandUse.objects.get(code="LU_0")
        UIProvenanceOverride.objects.create(
            domain="landuse",
            row_code=row.code,
            row_label=row.name,
            region=row.region,
            general_information="",
            status_information="",
            ziel_information="",
            is_active=True,
        )

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Gemäß GENESIS basiert der Ausgangswert")
        self.assertNotContains(response, "Regionaldatenbank Deutschland")

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
        # Stakeholder T21/T22 (PDF §2.4.3): 4 balance buttons collapsed
        # to 2 in Phase 4-C. The visible labels now say "Balance Solar"
        # and "Balance Wind" only.
        self.assertContains(response, "Balance Solar")
        self.assertContains(response, "Balance Wind")
        self.assertNotContains(response, "WS Balance Solar<")
        self.assertNotContains(response, "WS Balance Wind<")
        self.assertNotContains(response, "Sector + WS")
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
        # Post Phase 2-B: user manual is now in German (PDF §2.5.1 + §T32).
        self.assertContains(response, "Benutzerhandbuch")
        self.assertContains(response, "Schritt 1")
        self.assertContains(response, "Flächennutzung")
