"""
Phase C (T66) — BalanceJob carries region_code; worker dispatches in
that region's scope.

Phase B left a TODO at simulator/balance_jobs.py:37 — the worker
hardcoded DE. Phase C closes it: the queue endpoints stamp
payload['region_code'] from session at create time, and
run_balance_job wraps dispatch in region_scope so a BB user clicking
Balance computes against BB workspace, not DE.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse


class QueuedBalanceJobCarriesRegionCodeTests(TestCase):
    """Each ws_api_* endpoint stamps payload['region_code'] from session."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseC_balance_user", password="x", is_staff=False
        )
        self.client.login(username="phaseC_balance_user", password="x")
        # Set the active region in session via the switcher endpoint.
        self.client.post(
            reverse("simulator:set_active_region"),
            {"region_code": "DE"},
            HTTP_REFERER="/simulation/",
        )

    def _post_balance_endpoint(self, url_name):
        return self.client.post(reverse(url_name))

    def test_solar_ws_only_job_carries_region_DE(self):
        from simulator.models import BalanceJob

        # In settings.DEBUG=True the inline path runs; force-queue path by
        # mocking the inline-debug bypass to a no-op.
        with patch("simulator.ws_queue_api._run_balance_job_inline_debug", return_value=None):
            resp = self._post_balance_endpoint("simulator:ws_api_apply_balance")
        self.assertEqual(resp.status_code, 200)
        job = BalanceJob.objects.filter(created_by=self.user).order_by("-created_at").first()
        self.assertIsNotNone(job)
        self.assertEqual(
            job.payload.get("region_code"),
            "DE",
            "Queued BalanceJob must carry region_code from session payload.",
        )

    def test_solar_sector_ws_job_carries_region_BB(self):
        from simulator.models import BalanceJob, Region

        Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        # Switch session region.
        self.client.post(
            reverse("simulator:set_active_region"),
            {"region_code": "BB"},
            HTTP_REFERER="/simulation/",
        )
        with patch("simulator.ws_queue_api._run_balance_job_inline_debug", return_value=None):
            resp = self._post_balance_endpoint("simulator:ws_api_apply_full_balance")
        self.assertEqual(resp.status_code, 200)
        job = BalanceJob.objects.filter(created_by=self.user).order_by("-created_at").first()
        self.assertIsNotNone(job)
        self.assertEqual(job.payload.get("region_code"), "BB")


class WorkerWrapsDispatchInRegionScopeTests(TestCase):
    """run_balance_job sets the region thread-local before dispatching."""

    def setUp(self):
        from simulator.models import BalanceJob, Region

        Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseC_worker_user", password="x", is_staff=False
        )

    def test_worker_uses_region_from_payload(self):
        from simulator.models import BalanceJob
        from simulator.region_scope import get_current_region_code

        captured = {"region": None}

        def fake_apply(*args, **kwargs):
            captured["region"] = get_current_region_code()
            return {"success": True, "test": "ok"}

        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            created_by=self.user,
            payload={"region_code": "BB"},
        )
        with patch("simulator.balance_jobs.apply_balanced_landuse", side_effect=fake_apply):
            from simulator.balance_jobs import run_balance_job

            run_balance_job(job)
        self.assertEqual(
            captured["region"],
            "BB",
            "Worker must wrap dispatch in region_scope(payload['region_code']).",
        )

    def test_worker_defaults_DE_when_payload_missing_region(self):
        from simulator.models import BalanceJob
        from simulator.region_scope import get_current_region_code

        captured = {"region": None}

        def fake_apply(*args, **kwargs):
            captured["region"] = get_current_region_code()
            return {"success": True, "test": "ok"}

        # Pre-Phase-C job: payload has no region_code. Worker must default DE.
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            created_by=self.user,
            payload={},
        )
        with patch("simulator.balance_jobs.apply_balanced_landuse", side_effect=fake_apply):
            from simulator.balance_jobs import run_balance_job

            run_balance_job(job)
        self.assertEqual(captured["region"], "DE")
