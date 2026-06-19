from __future__ import annotations

import contextlib
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from simulator.balance_jobs import _json_safe, claim_next_job, recover_interrupted_jobs, run_balance_job
from simulator.middleware import OwnerScopeMiddleware
from simulator.models import BalanceJob, CalculationRun
from simulator.ws_queue_api import (
    _balance_job_timeout_seconds,
    _expire_balance_job_if_stale,
    _queue_or_reuse_balance_job,
)

class WBBalanceJobsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff_user = user_model.objects.create_user(
            username="wb_staff",
            password="x",
            is_staff=True,
        )
        cls.normal_user = user_model.objects.create_user(
            username="wb_user",
            password="x",
            is_staff=False,
        )

    def test_json_safe_converts_non_finite_values(self):
        payload = {
            "a": float("inf"),
            "b": [1.0, float("-inf"), float("nan")],
            "c": {"x": float("nan"), "ok": 3},
        }
        out = _json_safe(payload)
        self.assertIsNone(out["a"])
        self.assertEqual(out["b"][0], 1.0)
        self.assertIsNone(out["b"][1])
        self.assertIsNone(out["b"][2])
        self.assertIsNone(out["c"]["x"])
        self.assertEqual(out["c"]["ok"], 3)

    def test_run_balance_job_dispatches_solar_ws_only(self):
        job = BalanceJob(job_type=BalanceJob.TYPE_SOLAR_WS_ONLY, created_by=self.staff_user)
        with patch("simulator.balance_jobs.owner_scope", return_value=contextlib.nullcontext()):
            with patch("simulator.balance_jobs.ensure_user_workspace_data") as ensure_workspace:
                with patch("simulator.balance_jobs.apply_balanced_landuse", return_value={"ok": True}) as apply_ws:
                    result = run_balance_job(job)

        ensure_workspace.assert_called_once_with(self.staff_user, region_code="DE")
        apply_ws.assert_called_once_with(
            include_sector_balance=False,
            run_final_renewable_sync=True,
        )
        self.assertTrue(result["ok"])
        self.assertIn("run_id", result)
        self.assertEqual(result["summary"]["job_type"], BalanceJob.TYPE_SOLAR_WS_ONLY)

    def test_run_balance_job_dispatches_wind_ws_only_for_non_staff(self):
        job = BalanceJob(job_type=BalanceJob.TYPE_WIND_WS_ONLY, created_by=self.normal_user)
        with patch("simulator.balance_jobs.owner_scope", return_value=contextlib.nullcontext()):
            with patch("simulator.balance_jobs.ensure_user_workspace_data") as ensure_workspace:
                with patch("simulator.balance_jobs.apply_balanced_wind_landuse", return_value={"ok": True}) as apply_ws:
                    run_balance_job(job)

        # Phase C (T66): ensure_user_workspace_data now receives region_code
        # from BalanceJob.payload (default DE when payload empty).
        ensure_workspace.assert_called_once_with(self.normal_user, region_code="DE")
        apply_ws.assert_called_once_with(
            include_sector_balance=False,
            run_final_renewable_sync=True,
        )

    def test_run_balance_job_renewables_recalc_branch_creates_run(self):
        job = BalanceJob(job_type=BalanceJob.TYPE_RENEWABLES_RECALC, created_by=self.normal_user)

        with patch("simulator.balance_jobs.owner_scope", return_value=contextlib.nullcontext()):
            with patch("simulator.balance_jobs.recalc_all_renewables_full", return_value=7):
                with patch("simulator.balance_jobs.time.perf_counter", side_effect=[10.0, 10.0, 10.25, 10.25]):
                    result = run_balance_job(job)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["renewables_updated"], 7)
        self.assertEqual(result["duration_ms"], 250)
        self.assertTrue(CalculationRun.objects.filter(id=result["run_id"]).exists())

    def test_run_balance_job_landuse_recalc_branch_creates_run(self):
        job = BalanceJob(job_type=BalanceJob.TYPE_LANDUSE_RECALC, created_by=self.normal_user)

        with patch("simulator.balance_jobs.owner_scope", return_value=contextlib.nullcontext()):
            with patch(
                "simulator.balance_jobs.unified_recalc_all",
                return_value={
                    "input_renewables": 11,
                    "ws365_updated": True,
                    "final_renewables": 19,
                },
            ):
                with patch("simulator.balance_jobs.time.perf_counter", side_effect=[20.0, 20.0, 20.4, 20.4]):
                    result = run_balance_job(job)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["input_renewables"], 11)
        self.assertTrue(result["summary"]["ws365_updated"])
        self.assertEqual(result["summary"]["final_renewables"], 19)
        self.assertEqual(result["duration_ms"], 399)
        self.assertTrue(CalculationRun.objects.filter(id=result["run_id"]).exists())

    def test_run_balance_job_raises_for_unknown_job_type(self):
        job = BalanceJob(job_type="unknown_type", created_by=self.staff_user)
        with patch("simulator.balance_jobs.owner_scope", return_value=contextlib.nullcontext()):
            with self.assertRaises(ValueError):
                run_balance_job(job)

    def test_claim_next_job_returns_none_when_queue_empty(self):
        self.assertIsNone(claim_next_job())

    def test_claim_next_job_transitions_queued_to_running(self):
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_QUEUED,
            created_by=self.staff_user,
            attempts=2,
            error="old",
        )

        claimed = claim_next_job()
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.id, job.id)
        self.assertEqual(claimed.status, BalanceJob.STATUS_RUNNING)
        self.assertEqual(claimed.attempts, 3)
        self.assertEqual(claimed.error, "")
        self.assertIsNotNone(claimed.started_at)

    def test_recover_interrupted_jobs_requeues_running_job_after_worker_restart(self):
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_WIND_SECTOR_WS,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.normal_user,
            attempts=1,
            started_at=timezone.now() - timedelta(minutes=4),
            error="",
        )

        recovered = recover_interrupted_jobs()

        self.assertEqual(recovered, {"requeued": 1, "failed": 0})
        job.refresh_from_db()
        self.assertEqual(job.status, BalanceJob.STATUS_QUEUED)
        self.assertIsNone(job.started_at)
        self.assertIn("Recovered after worker restart", job.error)

    @override_settings(BALANCE_JOB_MAX_ATTEMPTS=2)
    def test_recover_interrupted_jobs_fails_job_at_retry_limit(self):
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_WIND_SECTOR_WS,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.normal_user,
            attempts=2,
            started_at=timezone.now() - timedelta(minutes=4),
        )

        recovered = recover_interrupted_jobs()

        self.assertEqual(recovered, {"requeued": 0, "failed": 1})
        job.refresh_from_db()
        self.assertEqual(job.status, BalanceJob.STATUS_FAILED)
        self.assertIsNotNone(job.finished_at)
        self.assertIn("retry limit", job.error)

class WBWSQueueApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user_a = user_model.objects.create_user(username="wb_queue_a", password="x")
        cls.user_b = user_model.objects.create_user(username="wb_queue_b", password="x")

    def setUp(self):
        self.client.force_login(self.user_a)

    @override_settings(BALANCE_JOB_RUNNING_TIMEOUT_SECONDS=15)
    def test_balance_job_timeout_seconds_enforces_minimum(self):
        self.assertEqual(_balance_job_timeout_seconds("BALANCE_JOB_RUNNING_TIMEOUT_SECONDS", 1200), 60)

    @override_settings(BALANCE_JOB_RUNNING_TIMEOUT_SECONDS="bad")
    def test_balance_job_timeout_seconds_handles_invalid_setting(self):
        self.assertEqual(_balance_job_timeout_seconds("BALANCE_JOB_RUNNING_TIMEOUT_SECONDS", 90), 90)

    def test_queue_or_reuse_returns_existing_active_job(self):
        existing = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_QUEUED,
            created_by=self.user_a,
            payload={"x": 1},
        )
        reused = _queue_or_reuse_balance_job(self.user_a, BalanceJob.TYPE_SOLAR_WS_ONLY, {"x": 2})
        self.assertEqual(reused.id, existing.id)
        self.assertEqual(BalanceJob.objects.count(), 1)

    def test_expire_balance_job_if_stale_running_marks_failed(self):
        old_started = timezone.now() - timedelta(hours=2)
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.user_a,
            started_at=old_started,
        )
        _expire_balance_job_if_stale(job)
        job.refresh_from_db()
        self.assertEqual(job.status, BalanceJob.STATUS_FAILED)
        self.assertIn("expired while running", job.error)

    def test_expire_balance_job_if_stale_queued_marks_failed(self):
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_QUEUED,
            created_by=self.user_a,
        )
        BalanceJob.objects.filter(id=job.id).update(created_at=timezone.now() - timedelta(hours=2))
        job.refresh_from_db()
        _expire_balance_job_if_stale(job)
        job.refresh_from_db()
        self.assertEqual(job.status, BalanceJob.STATUS_FAILED)
        self.assertIn("expired in queue", job.error)

    def test_ws_api_balance_job_status_forbidden_for_other_user(self):
        foreign_job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_QUEUED,
            created_by=self.user_b,
        )
        resp = self.client.get(
            reverse("simulator:ws_api_balance_job_status", kwargs={"job_id": foreign_job.id})
        )
        self.assertEqual(resp.status_code, 403)

    def test_ws_api_apply_balance_rejects_non_post(self):
        resp = self.client.get(reverse("simulator:ws_api_apply_balance"))
        self.assertEqual(resp.status_code, 405)

    @override_settings(DEBUG=True)
    def test_ws_api_apply_balance_inline_debug_path(self):
        with patch("simulator.balance_jobs.run_balance_job", return_value={"success": True, "inline": True}):
            resp = self.client.post(reverse("simulator:ws_api_apply_balance"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["inline"])

    @override_settings(DEBUG=False)
    def test_ws_api_apply_balance_queue_path(self):
        resp = self.client.post(reverse("simulator:ws_api_apply_balance"))
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["queued"])
        self.assertTrue(
            BalanceJob.objects.filter(
                id=payload["job_id"],
                job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
                created_by=self.user_a,
            ).exists()
        )

class WBOwnerScopeMiddlewareTests(SimpleTestCase):
    def test_non_staff_user_triggers_workspace_and_owner_scope(self):
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, is_staff=False, id=11),
        )

        with patch("simulator.middleware.reset_current_owner") as reset_owner:
            with patch("simulator.middleware.ensure_user_workspace_data") as ensure_workspace:
                with patch("simulator.middleware.set_current_owner") as set_owner:
                    middleware = OwnerScopeMiddleware(lambda req: "ok")
                    response = middleware(request)

        self.assertEqual(response, "ok")
        # Phase B (T65): middleware now passes the active region (default
        # DE when request.session is missing) to ensure_user_workspace_data.
        ensure_workspace.assert_called_once_with(request.user, region_code="DE")
        set_owner.assert_called_once_with(request.user)
        self.assertEqual(reset_owner.call_count, 2)

    def test_staff_user_gets_workspace_bootstrap_on_webapp_pages(self):
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, is_staff=True, id=22),
        )

        with patch("simulator.middleware.reset_current_owner") as reset_owner:
            with patch("simulator.middleware.ensure_user_workspace_data") as ensure_workspace:
                with patch("simulator.middleware.set_current_owner") as set_owner:
                    middleware = OwnerScopeMiddleware(lambda req: "ok")
                    response = middleware(request)

        self.assertEqual(response, "ok")
        ensure_workspace.assert_called_once_with(request.user, region_code="DE")
        set_owner.assert_called_once_with(request.user)
        self.assertEqual(reset_owner.call_count, 2)

    def test_reset_is_called_even_when_view_raises(self):
        request = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, is_staff=False, id=33),
        )

        def _boom(_request):
            raise RuntimeError("view failed")

        with patch("simulator.middleware.reset_current_owner") as reset_owner:
            with patch("simulator.middleware.ensure_user_workspace_data"):
                with patch("simulator.middleware.set_current_owner"):
                    middleware = OwnerScopeMiddleware(_boom)
                    with self.assertRaises(RuntimeError):
                        middleware(request)

        self.assertEqual(reset_owner.call_count, 2)
