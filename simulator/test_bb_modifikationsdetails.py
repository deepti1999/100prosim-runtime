"""Phase 6-B tests — T48-T52: variant-compare charts page.

Per PDF §2.5.5, the Modifikationsdetails page has 5 grouped-bar charts,
each with 4 series (Status, Basisszenario, Vorzustand, Aktueller Zustand).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse, RenewableData, VerbrauchData


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
