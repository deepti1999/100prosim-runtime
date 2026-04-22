"""Phase 6-B tests — T48-T52: variant-compare charts page.

Per PDF §2.5.5, the Modifikationsdetails page has 5 grouped-bar charts,
each with 4 series (Status, Basisszenario, Vorzustand, Aktueller Zustand).
"""
import json
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import (
    BaselineSnapshot,
    LandUse,
    RenewableData,
    ScenarioSnapshot,
    VerbrauchData,
)


class ModifikationsdetailsPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="mod_user", password="x")

        # Minimal seed so the 5 charts have rows to pull.
        for code, category, unit, status, ziel in [
            ("1",    "KLIK",              "GWh/a", 300.0, 280.0),
            ("2",    "Gebäudewärme",      "GWh/a", 500.0, 400.0),
            ("3",    "Prozesswärme",      "GWh/a", 350.0, 320.0),
            ("6",    "Mobile Anwendungen","GWh/a", 450.0, 330.0),
            ("5",    "Grundstoffe",       "TWh/a",  90.0,  80.0),
            ("1.1.2","Strom-Eff. Haush.", "%",     100.0,  95.0),
            ("1.1.3","Strom-Eff. HDL",    "%",     100.0,  95.0),
            ("1.1.4","Strom-Eff. GI",     "%",     100.0,  95.0),
            ("2.4", "Energet. Sanierung","%",       0.0,  85.0),
            ("2.8", "Wärmepumpen",       "%",       0.0, 2030.0),
        ]:
            VerbrauchData.objects.get_or_create(
                code=code, defaults={
                    "category": category, "unit": unit,
                    "status": status, "ziel": ziel, "is_calculated": False,
                },
            )

        for code, name, sv, tv in [
            ("9.1.1", "Wind onshore", 100.0, 700.0),
            ("9.1.2", "Solar Freiflächen", 30.0, 1200.0),
            ("9.1.3", "Wasserkraft+Geothermie", 19.0, 25.0),
            ("9.1.4", "Biobrennstoffe", 5.0, 4.5),
        ]:
            RenewableData.objects.get_or_create(
                code=code, defaults={
                    "name": name, "category": "renewable", "unit": "TWh/a",
                    "status_value": sv, "target_value": tv, "is_fixed": True,
                },
            )

        cls.root = LandUse(
            code="LU_ROOT", name="Root", status_ha=1000.0, target_ha=1000.0,
            user_percent=100.0, increase_limit_baseline_percent=100.0, parent=None,
        )
        cls.root.save(skip_cascade=True)
        for code, name in [("LU_2.1", "Solar Freiflächen"), ("LU_6", "Wind onshore")]:
            lu = LandUse(
                code=code, name=name, status_ha=100.0, target_ha=300.0,
                user_percent=2.0, increase_limit_baseline_percent=10.0, parent=cls.root,
            )
            lu.save(skip_cascade=True)

    def setUp(self):
        self.client.force_login(self.user)

    def test_page_returns_200(self):
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        self.assertEqual(response.status_code, 200)

    def test_renders_all_five_chart_titles_from_PDF(self):
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        # Exact German titles from PDF §2.5.5.
        self.assertContains(response, "Nachfrage-Einflüsse auf Endenergieverbrauch")
        self.assertContains(response, "Effizienz-Einflüsse auf Endenergieverbrauch")
        self.assertContains(response, "Endenergie-Verbrauch nach Anwendungsbereichen")
        self.assertContains(response, "Primärenergie-Beiträge nach Quellen")
        self.assertContains(response, "Ausbau der Erneuerbaren Energiequellen")

    def test_renders_four_series_labels_per_chart(self):
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        body = response.content.decode()
        # The 4-series legend is produced client-side; the JSON payload
        # carries the series keys.
        self.assertIn('"status"', body)
        self.assertIn('"basisszenario"', body)
        self.assertIn('"vorzustand"', body)
        self.assertIn('"aktuell"', body)

    def test_charts_have_correct_canvas_ids(self):
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        for canvas_id in [
            "chart_nachfrage_einfluesse",
            "chart_effizienz_einfluesse",
            "chart_endenergie_anwendungen",
            "chart_primaerenergie_quellen",
            "chart_ausbau_erneuerbare",
        ]:
            self.assertContains(response, f'id="{canvas_id}"')


class ModifikationsdetailsPopulatedStateTests(TestCase):
    """Exercises the full data path: admin baseline + scenario snapshot
    + live modification → all four chart series have values, not nulls.

    Closes gap #4 from docs/stakeholder/VERIFICATION_STATUS.md.
    """

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username="pm_admin", password="x", is_staff=True)
        cls.user = User.objects.create_user(username="pm_user", password="x")

        # Same domain seed as the main test class — owner=None so both the
        # admin workspace AND the user's workspace see these initial rows.
        for code, category, unit, status, ziel in [
            ("1",    "KLIK",              "GWh/a", 300.0, 280.0),
            ("2",    "Gebäudewärme",      "GWh/a", 500.0, 400.0),
            ("3",    "Prozesswärme",      "GWh/a", 350.0, 320.0),
            ("6",    "Mobile Anwendungen","GWh/a", 450.0, 330.0),
            ("5",    "Grundstoffe",       "TWh/a",  90.0,  80.0),
            ("1.1.2","Strom-Eff. Haush.", "%",     100.0,  95.0),
            ("1.1.3","Strom-Eff. HDL",    "%",     100.0,  95.0),
            ("1.1.4","Strom-Eff. GI",     "%",     100.0,  95.0),
            ("2.4", "Energet. Sanierung","%",       0.0,  85.0),
            ("2.8", "Wärmepumpen",       "%",       0.0, 2030.0),
        ]:
            VerbrauchData.objects.get_or_create(
                code=code, defaults={
                    "category": category, "unit": unit,
                    "status": status, "ziel": ziel, "is_calculated": False,
                },
            )
        for code, name, sv, tv in [
            ("9.1.1", "Wind onshore", 100.0, 700.0),
            ("9.1.2", "Solar Freiflächen", 30.0, 1200.0),
            ("9.1.3", "Wasserkraft+Geothermie", 19.0, 25.0),
            ("9.1.4", "Biobrennstoffe", 5.0, 4.5),
        ]:
            RenewableData.objects.get_or_create(
                code=code, defaults={
                    "name": name, "category": "renewable", "unit": "TWh/a",
                    "status_value": sv, "target_value": tv, "is_fixed": True,
                },
            )
        cls.root = LandUse(
            code="LU_ROOT", name="Root", status_ha=1000.0, target_ha=1000.0,
            user_percent=100.0, increase_limit_baseline_percent=100.0, parent=None,
        )
        cls.root.save(skip_cascade=True)
        for code, name, target_ha in [("LU_2.1", "Solar Freiflächen", 300.0),
                                      ("LU_6", "Wind onshore", 200.0)]:
            lu = LandUse(
                code=code, name=name, status_ha=100.0, target_ha=target_ha,
                user_percent=2.0, increase_limit_baseline_percent=10.0, parent=cls.root,
            )
            lu.save(skip_cascade=True)

    def _extract_chart_payload(self, response):
        """Pull the JSON from the <script id="modifikationsdetails-data"> tag."""
        body = response.content.decode()
        # Django's json_script emits: <script id="..." type="application/json">...</script>
        match = re.search(
            r'<script id="modifikationsdetails-data" type="application/json">(.*?)</script>',
            body, re.DOTALL,
        )
        self.assertIsNotNone(match, "json_script payload not found in response")
        return json.loads(match.group(1))

    def test_all_four_series_populated_end_to_end(self):
        """Full flow: admin creates baseline, user saves a scenario, user
        modifies a value, then /modifikationsdetails/ should render all 4
        series with non-null values.
        """
        # 1. Admin creates baseline (captures owner=None shared rows).
        self.client.force_login(self.admin)
        create_response = self.client.post(reverse("simulator:create_baseline"))
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(BaselineSnapshot.objects.count(), 1)

        # 2. Switch to regular user. Save a scenario snapshot to populate
        #    the Vorzustand series.
        self.client.logout()
        self.client.force_login(self.user)
        scenario_response = self.client.post(
            reverse("simulator:create_scenario"),
            data=json.dumps({"name": "vorzustand-test"}),
            content_type="application/json",
        )
        self.assertEqual(scenario_response.status_code, 200)
        self.assertEqual(ScenarioSnapshot.objects.filter(owner=self.user).count(), 1)

        # 3. User makes a modification: change one of the Verbrauch rows.
        self.client.post(
            reverse("simulator:save_verbrauch_user_input"),
            data=json.dumps({"code": "1.1.2", "user_percent": 80.0}),
            content_type="application/json",
        )

        # 4. Hit /modifikationsdetails/ and inspect the JSON payload.
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        self.assertEqual(response.status_code, 200)

        charts = self._extract_chart_payload(response)
        self.assertEqual(len(charts), 5, "expected all 5 variant-compare charts")

        for chart in charts:
            with self.subTest(chart=chart["id"]):
                s = chart["series"]
                # Status: always non-null (comes straight from the DB).
                self.assertTrue(
                    any(v is not None for v in s["status"]),
                    f"Status series empty on {chart['id']}"
                )
                # Aktueller Zustand: always non-null.
                self.assertTrue(
                    any(v is not None for v in s["aktuell"]),
                    f"Aktueller-Zustand series empty on {chart['id']}"
                )
                # Basisszenario: should be populated now that admin baseline exists.
                self.assertTrue(
                    any(v is not None for v in s["basisszenario"]),
                    f"Basisszenario series empty on {chart['id']} despite admin baseline"
                )
                # Vorzustand: populated via the user's ScenarioSnapshot.
                self.assertTrue(
                    any(v is not None for v in s["vorzustand"]),
                    f"Vorzustand series empty on {chart['id']} despite saved scenario"
                )

    def test_vorzustand_falls_back_to_baseline_when_no_scenario(self):
        """If user has no ScenarioSnapshot yet, Vorzustand should fall
        back to the admin Basisszenario (not stay null).
        """
        self.client.force_login(self.admin)
        self.client.post(reverse("simulator:create_baseline"))

        self.client.logout()
        self.client.force_login(self.user)
        # No scenario created -- vorzustand should still be populated from admin baseline.
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        charts = self._extract_chart_payload(response)
        for chart in charts:
            with self.subTest(chart=chart["id"]):
                s = chart["series"]
                # With an admin baseline but no scenario, both basis + vorzustand
                # should be populated (vorzustand falls back to baseline).
                self.assertTrue(any(v is not None for v in s["basisszenario"]))
                self.assertTrue(any(v is not None for v in s["vorzustand"]))

    def test_empty_state_renders_gracefully(self):
        """No admin baseline + no scenario: page still renders, series
        for basis + vorzustand contain nulls, user sees the warning
        notice.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("simulator:modifikationsdetails"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Noch kein Basisszenario vom Administrator erstellt")

        charts = self._extract_chart_payload(response)
        for chart in charts:
            with self.subTest(chart=chart["id"]):
                s = chart["series"]
                # Status + Aktuell always live, regardless of snapshots.
                self.assertTrue(any(v is not None for v in s["status"]))
                self.assertTrue(any(v is not None for v in s["aktuell"]))
                # Basis + Vorzustand should both be all-null.
                self.assertTrue(all(v is None for v in s["basisszenario"]))
                self.assertTrue(all(v is None for v in s["vorzustand"]))
