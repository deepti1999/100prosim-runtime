import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import LandUse

class BlackBoxValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="bb_val_admin",
            password="test-pass-123",
            is_staff=True,
        )

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

    def test_landuse_update_rejects_over_limit_increase(self):
        response = self._post_json(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.child.pk}),
            {"user_percent": 14.0},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["status"], "error")
        self.assertIn("max_allowed_value", payload)

    def test_landuse_update_accepts_valid_increase(self):
        response = self._post_json(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.child.pk}),
            {"user_percent": 13.0},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["code"], "LU_2.1")

        updated = LandUse.all_objects.get(owner=self.user, code=self.child.code)
        self.assertAlmostEqual(updated.user_percent, 13.0)

    def test_landuse_update_rejects_root_node(self):
        response = self._post_json(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.root.pk}),
            {"user_percent": 50.0},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["status"], "error")
        self.assertIn("root level", payload["message"].lower())

    def test_save_verbrauch_user_input_rejects_missing_code(self):
        response = self._post_json(
            reverse("simulator:save_verbrauch_user_input"),
            {"user_percent": 22.0},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(payload["success"])
        self.assertIn("missing code", payload["error"].lower())

    def test_landuse_update_requires_post(self):
        response = self.client.get(
            reverse("simulator:update_landuse_percent", kwargs={"pk": self.child.pk})
        )
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["status"], "error")
        self.assertIn("post method required", payload["message"].lower())
