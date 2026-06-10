from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache as django_cache
from django.test import TestCase

from simulator import recalc_cache
from simulator.balance_jobs import run_balance_job
from simulator.models import BalanceJob, CalculationRun


class BalanceJobCacheInvalidationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="balance_cache_user",
            password="x",
        )

    @patch("simulator.balance_jobs.apply_balanced_landuse")
    def test_ws_balance_job_creates_calculation_run_for_bilanz_cache(self, mocked_balance):
        mocked_balance.return_value = {
            "success": True,
            "storage_drift": 0.0,
            "annual_electricity": 1000.0,
            "landuse_code": "LU_2.1",
        }
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.user,
            payload={"region_code": "DE"},
        )
        recalc_cache._cache["stale-balance-job"] = (1, {"old": True})
        django_cache.set("stale-bilanz-job", {"old": True}, timeout=60)

        result = run_balance_job(job)

        self.assertEqual(CalculationRun.objects.count(), 1)
        run = CalculationRun.objects.get()
        self.assertEqual(result["run_id"], run.id)
        self.assertEqual(run.summary["job_type"], BalanceJob.TYPE_SOLAR_WS_ONLY)
        self.assertEqual(run.summary["scope"], "balance_job")
        self.assertEqual(run.summary["storage_drift"], 0.0)
        self.assertEqual(recalc_cache._cache, {})
        self.assertIsNone(django_cache.get("stale-bilanz-job"))

    @patch("simulator.balance_jobs._run_verbrauch_recalc_passes")
    def test_recalc_jobs_keep_their_existing_calculation_run(self, mocked_recalc):
        mocked_recalc.return_value = {
            "success": True,
            "updated_count": 0,
            "passes": 1,
            "per_pass_updates": [],
            "stabilized": True,
        }
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_VERBRAUCH_RECALC,
            status=BalanceJob.STATUS_RUNNING,
            created_by=self.user,
            payload={"region_code": "DE"},
        )

        result = run_balance_job(job)

        self.assertEqual(CalculationRun.objects.count(), 1)
        self.assertEqual(result["run_id"], CalculationRun.objects.get().id)
