import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import RenewableData

class BlackBoxRenewableUserEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="bb_renewable_edit_admin",
            password="test-pass-123",
            is_staff=True,
        )
        RenewableData.objects.create(
            code="99.99.1",
            name="Editable renewable input",
            category="renewable",
            unit="GWh/a",
            status_value=10.0,
            target_value=20.0,
            user_input=20.0,
            is_fixed=True,
            user_editable=True,
        )
        RenewableData.objects.create(
            code="99.99.2",
            name="Locked renewable input",
            category="renewable",
            unit="GWh/a",
            status_value=10.0,
            target_value=20.0,
            is_fixed=True,
            user_editable=False,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _post_json(self, payload):
        return self.client.post(
            reverse("simulator:save_renewable_user_input"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_save_renewable_user_input_updates_target_for_editable_row(self):
        response = self._post_json({"code": "99.99.1", "user_input": 33.5})
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["code"], "99.99.1")

        updated = RenewableData.objects.get(code="99.99.1")
        self.assertAlmostEqual(updated.user_input, 33.5)
        self.assertAlmostEqual(updated.target_value, 33.5)

    def test_save_renewable_user_input_rejects_non_editable_row(self):
        response = self._post_json({"code": "99.99.2", "user_input": 44.0})
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(payload["success"])
        self.assertIn("not enabled", payload["error"])

    def test_save_renewable_user_input_rejects_missing_code(self):
        response = self._post_json({"user_input": 12.0})
        payload = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(payload["success"])
        self.assertIn("Missing code", payload["error"])

