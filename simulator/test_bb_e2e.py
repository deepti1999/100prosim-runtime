import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse, RenewableData, VerbrauchData

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

class BlackBoxE2EWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="bb_e2e_admin",
            password="test-pass-123",
            is_staff=True,
        )
        _seed_ws_fixed_dependencies()

        cls.root = LandUse(
            code="LU_ROOT",
            name="Root",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=None,
        )
        cls.root.save(skip_cascade=True)

        cls.child = LandUse(
            code="LU_2.1",
            name="Solar Land",
            status_ha=100.0,
            target_ha=100.0,
            user_percent=10.0,
            increase_limit_baseline_percent=10.0,
            parent=cls.root,
        )
        cls.child.save(skip_cascade=True)

    def setUp(self):
        self.client.force_login(self.user)

    def _post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_e2e_landuse_update_then_recalc_keeps_persisted_state_consistent(self):
        update_response = self._post_json(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.child.pk}),
            {"user_percent": 12.0},
        )
        update_payload = update_response.json()

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_payload["status"], "ok")

        recalc_response = self.client.post(reverse("simulator:run_full_recalc"))
        recalc_payload = recalc_response.json()
        self.assertEqual(recalc_response.status_code, 200)
        self.assertEqual(recalc_payload["status"], "ok")

        persisted = LandUse.all_objects.get(owner=self.user, code="LU_2.1")
        self.assertAlmostEqual(persisted.user_percent, 12.0)
        self.assertAlmostEqual(persisted.target_ha, 120.0)

        landuse_page = self.client.get(reverse("simulator:landuse_list"))
        self.assertEqual(landuse_page.status_code, 200)
        self.assertContains(landuse_page, "LU_2.1")

    def test_e2e_baseline_create_mutate_restore_roundtrip(self):
        create_response = self.client.post(reverse("simulator:create_baseline"))
        create_payload = create_response.json()
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_payload["status"], "ok")

        mutate_response = self._post_json(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.child.pk}),
            {"user_percent": 12.0},
        )
        self.assertEqual(mutate_response.status_code, 200)
        mutated = LandUse.all_objects.get(owner=self.user, code="LU_2.1")
        self.assertAlmostEqual(mutated.user_percent, 12.0)

        restore_response = self.client.post(reverse("simulator:restore_baseline"))
        restore_payload = restore_response.json()
        self.assertEqual(restore_response.status_code, 200)
        self.assertEqual(restore_payload["status"], "ok")

        restored = LandUse.all_objects.get(owner=self.user, code="LU_2.1")
        self.assertAlmostEqual(restored.user_percent, 10.0)
        self.assertAlmostEqual(restored.target_ha, 100.0)
