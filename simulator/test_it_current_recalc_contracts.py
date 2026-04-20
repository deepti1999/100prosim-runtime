"""Integration tests for the current recalculation entry-point contracts."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from simulator.models import BalanceJob, LandUse

class CurrentRecalculationContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="it_recalc_user",
            password="test-pass-123",
        )
        cls.root = LandUse.objects.create(
            owner=cls.user,
            code="LU_ROOT",
            name="Root",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=None,
        )
        cls.child = LandUse.objects.create(
            owner=cls.user,
            code="LU_2.1",
            name="Solar Land",
            status_ha=100.0,
            target_ha=100.0,
            user_percent=10.0,
            increase_limit_baseline_percent=10.0,
            parent=cls.root,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _post_json(self, url, payload, **extra):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            **extra,
        )

    @patch("simulator.views.unified_recalc_all")
    def test_landuse_save_all_inline_contract_matches_current_app(self, mock_recalc):
        mock_recalc.return_value = {
            "input_renewables": 7,
            "ws365_updated": True,
            "final_renewables": 9,
        }

        response = self._post_json(
            reverse("simulator:save_all_inputs"),
            {"user_inputs": {"LU_2.1": 12.0}},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertFalse(payload["queued"])
        self.assertEqual(payload["saved_count"], 1)
        self.assertEqual(len(payload["changes"]), 1)
        self.assertEqual(payload["summary"]["input_renewables"], 7)
        self.assertTrue(payload["summary"]["ws365_updated"])
        self.assertEqual(payload["summary"]["final_renewables"], 9)

        updated = LandUse.all_objects.get(pk=self.child.pk)
        self.assertAlmostEqual(updated.user_percent, 12.0)
        self.assertAlmostEqual(updated.target_ha, 120.0)
        mock_recalc.assert_called_once()

    @override_settings(DEBUG=False)
    def test_landuse_save_all_hosted_contract_queues_landuse_job(self):
        response = self._post_json(
            reverse("simulator:save_all_inputs"),
            {"user_inputs": {"LU_2.1": 12.5}},
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["queued"])
        self.assertEqual(payload["saved_count"], 1)
        self.assertTrue(
            BalanceJob.objects.filter(
                id=payload["job_id"],
                job_type=BalanceJob.TYPE_LANDUSE_RECALC,
                created_by=self.user,
            ).exists()
        )

    @patch("simulator.input_api.recalc_all_verbrauch")
    def test_verbrauch_save_recalculate_inline_runs_multi_pass_until_stable(self, mock_recalc):
        mock_recalc.side_effect = [
            ["2.1", "2.2"],
            ["2.2"],
            [],
        ]

        response = self.client.post(reverse("simulator:save_recalc_verbrauch"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["updated_count"], 2)
        self.assertEqual(payload["passes"], 3)
        self.assertEqual(payload["per_pass_updates"], [2, 1, 0])
        self.assertTrue(payload["stabilized"])
        self.assertEqual(mock_recalc.call_count, 3)

    @override_settings(DEBUG=False)
    def test_verbrauch_save_recalculate_hosted_contract_queues_job(self):
        response = self.client.post(
            reverse("simulator:save_recalc_verbrauch"),
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["queued"])
        self.assertTrue(
            BalanceJob.objects.filter(
                id=payload["job_id"],
                job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
                created_by=self.user,
            ).exists()
        )
