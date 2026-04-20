from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import Formula, RenewableData, VerbrauchData

def _seed_ws_fixed_dependencies():
    required_verbrauch = [
        ("7", "Total demand", "GWh", 0.0, 1000.0),
        ("2.9.2", "Raumwaerme demand", "GWh", 0.0, 120.0),
        ("2.4", "Raumwaerme percent", "%", 0.0, 35.0),
    ]
    for code, category, unit, status, ziel in required_verbrauch:
        VerbrauchData.objects.get_or_create(
            code=code,
            defaults={
                "category": category,
                "unit": unit,
                "status": status,
                "ziel": ziel,
                "is_calculated": False,
            },
        )

    required_renewables = [
        ("9.1.1", "Wind", 420.0),
        ("9.1.2", "Solar", 380.0),
        ("9.1.3", "Other", 200.0),
        ("9.1.4", "Bio", 90.0),
        ("9.2.1.5.2", "Subtraction", 60.0),
    ]
    for code, name, target_value in required_renewables:
        RenewableData.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "category": "renewable",
                "unit": "GWh",
                "status_value": 0.0,
                "target_value": target_value,
                "is_fixed": True,
            },
        )

class BlackBoxCalculationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="bb_calc_admin",
            password="test-pass-123",
            is_staff=True,
        )
        _seed_ws_fixed_dependencies()

        VerbrauchData.objects.bulk_create(
            [
                VerbrauchData(
                    code="1",
                    category="KLIK total",
                    unit="GWh",
                    status=0.0,
                    ziel=0.0,
                    is_calculated=True,
                    status_calculated=True,
                    ziel_calculated=True,
                ),
                VerbrauchData(
                    code="1.1",
                    category="KLIK child",
                    unit="GWh",
                    status=10.0,
                    ziel=20.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="1.4",
                    category="KLIK total (Bilanz)",
                    unit="GWh",
                    status=10.0,
                    ziel=20.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="2.10",
                    category="GW total (Bilanz)",
                    unit="GWh",
                    status=0.0,
                    ziel=0.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="3.7",
                    category="PW total (Bilanz)",
                    unit="GWh",
                    status=0.0,
                    ziel=0.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="6.0",
                    category="Mobile total (Bilanz)",
                    unit="GWh",
                    status=0.0,
                    ziel=0.0,
                    is_calculated=False,
                ),
            ]
        )

        Formula.objects.create(
            key="V_1",
            category="verbrauch",
            formula_type="status",
            expression="Verbrauch_1_1",
            is_active=True,
        )
        Formula.objects.create(
            key="V_1",
            category="verbrauch",
            formula_type="ziel",
            expression="Verbrauch_1_1",
            is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_run_full_recalc_returns_structured_payload(self):
        response = self.client.post(reverse("simulator:run_full_recalc"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("run_id", payload)
        self.assertIn("duration_ms", payload)
        self.assertIn("summary", payload)
        self.assertIn("renewables_updated", payload["summary"])
        self.assertIn("verbrauch_updated", payload["summary"])

    def test_recalc_verbrauch_updates_expected_parent_values(self):
        response = self.client.post(reverse("simulator:recalc_verbrauch"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "ok")

        parent = VerbrauchData.objects.get(code="1")
        self.assertAlmostEqual(parent.status, 10.0)
        self.assertAlmostEqual(parent.ziel, 20.0)

    def test_save_recalc_verbrauch_returns_expected_contract(self):
        response = self.client.post(reverse("simulator:save_recalc_verbrauch"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertIn("updated_count", payload)
        self.assertIn("passes", payload)
        self.assertIn("per_pass_updates", payload)
        self.assertIn("stabilized", payload)

    def test_bilanz_page_exposes_ws_balance_status_context(self):
        response = self.client.get(reverse("simulator:bilanz"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("ws_balance_status", response.context)
        self.assertEqual(response.context["ws_balance_status"]["tolerance"], 0.1)
