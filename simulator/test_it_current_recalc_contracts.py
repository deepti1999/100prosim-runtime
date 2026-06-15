"""Integration tests for the current recalculation entry-point contracts."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from simulator.models import BalanceJob, LandUse, VerbrauchData

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
        cls.verbrauch = VerbrauchData.objects.create(
            owner=cls.user,
            code="1.1.2",
            category="Stromanwendungs-Effizienz Haushalte",
            unit="%",
            status=100.0,
            ziel=100.0,
            user_percent=100.0,
            user_editable=True,
        )
        cls.staff_user = get_user_model().objects.create_user(
            username="it_recalc_staff",
            password="test-pass-123",
            is_staff=True,
        )
        cls.staff_scope_code = "STAFF_SCOPE"
        cls.global_staff_scope_row = VerbrauchData.all_objects.create(
            owner=None,
            code=cls.staff_scope_code,
            category="Global staff scope guard",
            unit="%",
            status=100.0,
            ziel=100.0,
            user_percent=100.0,
            user_editable=True,
        )
        cls.staff_scope_row = VerbrauchData.all_objects.create(
            owner=cls.staff_user,
            code=cls.staff_scope_code,
            category="Staff workspace scope guard",
            unit="%",
            status=100.0,
            ziel=100.0,
            user_percent=100.0,
            user_editable=True,
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

    @override_settings(DEBUG=False)
    def test_landuse_save_after_active_job_queues_fresh_recalc_job(self):
        old_job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_LANDUSE_RECALC,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.user,
            started_at=timezone.now(),
            payload={"scope": "landuse", "old": True},
        )

        response = self._post_json(
            reverse("simulator:save_all_inputs"),
            {"user_inputs": {"LU_2.1": 12.75}},
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["queued"])
        self.assertNotEqual(payload["job_id"], str(old_job.id))
        self.assertEqual(
            BalanceJob.objects.filter(
                job_type=BalanceJob.TYPE_LANDUSE_RECALC,
                created_by=self.user,
                status__in=[BalanceJob.STATUS_QUEUED, BalanceJob.STATUS_RUNNING],
            ).count(),
            2,
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

    @override_settings(DEBUG=False)
    def test_verbrauch_cell_save_after_active_job_queues_fresh_recalc_job(self):
        old_job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.user,
            started_at=timezone.now(),
            payload={"scope": "verbrauch", "old": True},
        )

        response = self._post_json(
            reverse("simulator:save_verbrauch_user_input"),
            {"code": "1.1.2", "user_percent": 95.0},
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertNotEqual(payload["recalc_job_id"], str(old_job.id))
        self.assertEqual(
            BalanceJob.objects.filter(
                job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
                created_by=self.user,
                status__in=[BalanceJob.STATUS_QUEUED, BalanceJob.STATUS_RUNNING],
            ).count(),
            2,
        )

    @patch("simulator.models.VerbrauchData._recalculate_dependents")
    def test_verbrauch_cell_save_queues_dependency_cascade_without_blocking(self, mock_cascade):
        response = self._post_json(
            reverse("simulator:save_verbrauch_user_input"),
            {"code": "1.1.2", "user_percent": 96.0},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])

        updated = VerbrauchData.all_objects.get(pk=self.verbrauch.pk)
        self.assertAlmostEqual(updated.user_percent, 96.0)
        self.assertAlmostEqual(updated.ziel, 96.0)
        mock_cascade.assert_not_called()
        self.assertTrue(payload["recalc_job_id"])
        self.assertTrue(
            BalanceJob.objects.filter(
                id=payload["recalc_job_id"],
                job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
                created_by=self.user,
            ).exists()
        )

    def test_staff_user_webapp_save_uses_personal_workspace_not_global_rows(self):
        self.client.force_login(self.staff_user)

        response = self._post_json(
            reverse("simulator:save_verbrauch_user_input"),
            {"code": self.staff_scope_code, "user_percent": 88.0},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        staff_row = VerbrauchData.all_objects.get(pk=self.staff_scope_row.pk)
        global_row = VerbrauchData.all_objects.get(pk=self.global_staff_scope_row.pk)
        self.assertAlmostEqual(staff_row.user_percent, 88.0)
        self.assertAlmostEqual(staff_row.ziel, 88.0)
        self.assertAlmostEqual(global_row.user_percent, 100.0)
        self.assertAlmostEqual(global_row.ziel, 100.0)

    @patch("simulator.balance_jobs.ensure_user_workspace_data")
    @patch("simulator.balance_jobs._run_verbrauch_recalc_passes")
    def test_verbrauch_worker_prepares_staff_workspace_scope(self, mock_recalc, mock_ensure_workspace):
        from simulator.balance_jobs import run_balance_job
        from simulator.owner_scope import get_current_owner_id

        def fake_recalc(*, triggered_by):
            self.assertEqual(triggered_by, self.staff_user.username)
            self.assertEqual(get_current_owner_id(), self.staff_user.id)
            return {
                "success": True,
                "updated_count": 0,
                "passes": 1,
                "per_pass_updates": [0],
                "stabilized": True,
            }

        mock_recalc.side_effect = fake_recalc
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.staff_user,
            started_at=timezone.now(),
            payload={"scope": "verbrauch", "region_code": "DE"},
        )

        result = run_balance_job(job)

        self.assertTrue(result["success"])
        mock_ensure_workspace.assert_called_once_with(self.staff_user, region_code="DE")
