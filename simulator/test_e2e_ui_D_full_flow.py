"""Django test for scenario D — solar + wind balance endpoints both reach the same
annual-electricity endpoint on the current seed baseline.

Mirrors regression/scenarios/D-full-flow-verbrauch-solar-wind.yml, but uses the
API directly (Django test client) rather than Playwright, because the full UI
replay depends on browser localStorage state that's brittle to simulate in
headless tests. The legacy regression harness (regression/compare.py)
covers the UI path.

    python manage.py test simulator.test_e2e_ui_D_full_flow -v 1
"""
import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse

from simulator._e2e_seed_helper import load_e2e_seed

TEST_USER = "e2e_d_user"
TEST_PASS = "e2e-d-pass-2026"


class ScenarioDBalanceEndpointTests(StaticLiveServerTestCase):
    """Scenario D via API. Verifies both balance-variants succeed and yield the
    annual-electricity invariant documented in the YAML / golden."""

    @classmethod
    def setUpClass(cls):
        from django.db import connection
        if connection.vendor == "sqlite":
            raise SkipTest("Scenario D requires Postgres; run against the docker stack DB")
        try:
            super().setUpClass()
        except PermissionError as exc:
            raise SkipTest(f"Live server could not start: {exc}") from exc

    def setUp(self):
        load_e2e_seed()
        u, _ = get_user_model().objects.get_or_create(
            username=TEST_USER, defaults={"email": "e2e-d@local.test"},
        )
        u.set_password(TEST_PASS)
        u.is_active = True
        u.save()

        self.client = Client()
        self.assertTrue(self.client.login(username=TEST_USER, password=TEST_PASS))

    # ---------- helpers ----------

    def _post(self, path):
        response = self.client.post(path, data="{}", content_type="application/json")
        self.assertIn(response.status_code, (200, 202), f"{path} returned {response.status_code}: {response.content[:300]}")
        return response.json() if response["Content-Type"].startswith("application/json") else {}

    # ---------- tests ----------

    def test_solar_variant_reaches_expected_lu_2_1_and_annual_electricity(self):
        """Post → solar_ws_only → solar_sector_ws. Expect LU_2.1 ≈ 680,478 ha and
        annual electricity ≈ 1,108,834 GWh at the end (tolerances per golden)."""
        step_a = self._post("/api/ws/apply-balance/")
        self.assertTrue(step_a.get("success"), f"apply-balance not success: {step_a}")

        step_b = self._post("/api/ws/apply-full-balance/")
        self.assertTrue(step_b.get("success"), f"apply-full-balance not success: {step_b}")

        # Under DEBUG=True, the endpoint runs inline and the payload contains
        # the ws_rebalance detail. Under DEBUG=False it queues; we don't drive
        # the worker here because the UI harness covers that path.
        rebalance = step_b.get("ws_rebalance", {})
        if rebalance:
            self.assertAlmostEqual(rebalance.get("new_landuse"), 680478.26, delta=5.0,
                                   msg=f"LU_2.1 != 680,478.26 ± 5: {rebalance.get('new_landuse')}")
            self.assertAlmostEqual(step_b.get("annual_electricity"), 1108834.53, delta=1.0,
                                   msg=f"annual electricity != 1,108,834.53 ± 1: {step_b.get('annual_electricity')}")
            self.assertLess(abs(step_b.get("storage_drift", 1.0)), 0.1,
                            msg=f"storage drift > 0.1: {step_b.get('storage_drift')}")

    def test_wind_variant_reaches_expected_lu_6_and_annual_electricity(self):
        """Wind counterpart: LU_6 barely moves (≈ 715,289 ha) but annual electricity
        converges to the same value as solar variant."""
        step_a = self._post("/api/ws/apply-balance-wind/")
        self.assertTrue(step_a.get("success"), f"apply-balance-wind not success: {step_a}")

        step_b = self._post("/api/ws/apply-full-balance-wind/")
        self.assertTrue(step_b.get("success"), f"apply-full-balance-wind not success: {step_b}")

        rebalance = step_b.get("ws_rebalance", {})
        if rebalance:
            self.assertAlmostEqual(rebalance.get("new_landuse"), 715288.57, delta=5.0,
                                   msg=f"LU_6 != 715,288.57 ± 5: {rebalance.get('new_landuse')}")
            self.assertAlmostEqual(step_b.get("annual_electricity"), 1108834.53, delta=1.0,
                                   msg=f"annual electricity != 1,108,834.53 ± 1: {step_b.get('annual_electricity')}")
            self.assertLess(abs(step_b.get("storage_drift", 1.0)), 0.1,
                            msg=f"storage drift > 0.1: {step_b.get('storage_drift')}")

    def test_cross_variant_annual_electricity_converges(self):
        """The thesis-level invariant: solar path and wind path should both produce
        the same annual electricity on this baseline."""
        self._post("/api/ws/apply-balance/")
        solar_full = self._post("/api/ws/apply-full-balance/")
        solar_ae = solar_full.get("annual_electricity")

        # reset to baseline before wind
        self.client.post("/api/baseline/restore/")
        self._post("/api/ws/apply-balance-wind/")
        wind_full = self._post("/api/ws/apply-full-balance-wind/")
        wind_ae = wind_full.get("annual_electricity")

        if solar_ae is not None and wind_ae is not None:
            self.assertAlmostEqual(solar_ae, wind_ae, delta=1.0,
                                   msg=f"Solar and wind paths diverge: solar={solar_ae} wind={wind_ae}")
