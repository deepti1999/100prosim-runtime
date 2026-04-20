"""Playwright-driven baseline smoke tests (mirrors regression/scenarios/A-baseline-readonly.yml).

Runs against a Django LiveServer with the seed fixture loaded. Skips cleanly if
Playwright isn't installed or Chromium isn't available, so the core test suite
still passes in minimal environments.

    python manage.py test simulator.test_e2e_ui_baseline -v 1
"""

import os

# Playwright's sync API internally drives asyncio. Django flags synchronous DB
# calls from "async context" as unsafe — in tests we know the sync calls are
# serialized, so opt out of the guard. Must be set BEFORE Django touches DBs.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from simulator._e2e_seed_helper import load_e2e_seed

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
    PlaywrightError = Exception


TEST_USER = "e2e_ui_user"
TEST_PASS = "e2e-ui-pass-2026"


class UIBaselineTests(StaticLiveServerTestCase):
    """Login + visit each main page. Asserts stable UI labels and seeded row counts.

    LiveServerTestCase is a TransactionTestCase → the DB is flushed between test
    methods, so seed + user are reloaded in setUp rather than setUpClass.
    """

    @classmethod
    def setUpClass(cls):
        from django.db import connection
        if connection.vendor == "sqlite":
            # The project's middleware opens transaction.atomic() per request, which
            # nests badly under TransactionTestCase + SQLite + Playwright's
            # concurrent fetches. Postgres handles this fine. Tests here are designed
            # to run against the docker Postgres; skip on SQLite to avoid false
            # failures. Run with LOCAL_POSTGRES_URL=... for correct results.
            raise SkipTest("UI e2e tests require Postgres; run against the docker stack DB")

        try:
            super().setUpClass()
        except PermissionError as exc:
            raise SkipTest(f"Live server could not start: {exc}") from exc

        if sync_playwright is None:
            raise SkipTest("playwright not installed; pip install -r requirements-dev.txt")

        try:
            cls._pw = sync_playwright().start()
            cls._browser = cls._pw.chromium.launch(headless=True)
        except PlaywrightError as exc:
            raise SkipTest(f"Chromium unavailable (run `python -m playwright install chromium`): {exc}") from exc

    @classmethod
    def tearDownClass(cls):
        browser = getattr(cls, "_browser", None)
        if browser is not None:
            browser.close()
        pw = getattr(cls, "_pw", None)
        if pw is not None:
            pw.stop()
        super().tearDownClass()

    def setUp(self):
        # Seed + user get reloaded per test because TransactionTestCase flushes the DB.
        load_e2e_seed()
        u, _ = get_user_model().objects.get_or_create(
            username=TEST_USER, defaults={"email": "e2e-ui@local.test"},
        )
        u.set_password(TEST_PASS)
        u.is_active = True
        u.save()

        self.context = self._browser.new_context()
        self.page = self.context.new_page()
        self._login()

    def tearDown(self):
        self.context.close()

    def _url(self, name):
        return f"{self.live_server_url}{reverse(name)}"

    def _login(self):
        self.page.goto(f"{self.live_server_url}/login/")
        self.page.fill("input[name='username']", TEST_USER)
        self.page.fill("input[name='password']", TEST_PASS)
        # Click the submit button so Django's CSRF + form validation runs normally.
        self.page.locator("form button[type='submit'], form button.btn-login, form button").first.click()
        self.page.wait_for_url("**/simulation/", timeout=15000)

    # ---------- tests ----------

    def test_simulation_dashboard_shows_seeded_counts(self):
        self.page.goto(self._url("simulator:main_simulation"))
        self.assertEqual(self.page.title(), "Simulations-Übersicht")
        body = self.page.inner_text("body")
        # Dashboard cards derived from seed: LU=20, Renewable=223, Verbrauch editable=45
        self.assertIn("20", body)
        self.assertIn("223", body)
        self.assertIn("45", body)

    def test_landuse_page_lists_20_rows_with_known_codes(self):
        self.page.goto(self._url("simulator:landuse_list"))
        row_count = self.page.locator("table tbody tr").count()
        self.assertEqual(row_count, 20)
        body = self.page.inner_text("body")
        for code in ("LU_0", "LU_1", "LU_2.1", "LU_3", "LU_6"):
            self.assertIn(code, body)

    def test_renewable_page_carries_ws_balance_anchor_values(self):
        self.page.goto(self._url("simulator:renewable_list"))
        # 9.3.1 and 9.3.4 are the WS-balance-anchor rows per thesis scenario C.
        # Target values are seeded: 406,403.3 and 195,890.3.
        row_931 = self.page.locator("[data-code='9.3.1']").first.locator("xpath=ancestor::tr").inner_text()
        row_934 = self.page.locator("[data-code='9.3.4']").first.locator("xpath=ancestor::tr").inner_text()
        self.assertIn("406,403.3", row_931)
        self.assertIn("195,890.3", row_934)

    def test_annual_electricity_svg_has_all_known_flow_classes(self):
        self.page.goto(self._url("simulator:annual_electricity"))
        # Flow diagram uses SVG text with classes txt-flow, txt-value-sm, etc.
        # Presence of these classes is a proxy for "the diagram rendered".
        for cls in ("txt-flow", "txt-value-sm", "txt-flow-sm", "txt-node-value"):
            count = self.page.locator(f"svg text.{cls}").count()
            self.assertGreater(count, 0, f"expected svg text.{cls} to exist")

    def test_bilanz_page_shows_status_and_ziel_sections(self):
        self.page.goto(self._url("simulator:bilanz"))
        # Page has two tabs; inner_html picks up the Ziel section even when the Status tab is active.
        html = self.page.inner_html("body")
        self.assertIn("Bilanz Endenergie", html)
        self.assertIn("Status Bilanz Endenergie", html)
        self.assertIn("Ziel Bilanz Endenergie", html)

    def test_cockpit_shows_total_endenergieverbrauch(self):
        self.page.goto(self._url("simulator:cockpit"))
        body = self.page.inner_text("body")
        self.assertIn("Gesamt Endenergieverbrauch", body)
        self.assertIn("Erneuerbarer Anteil", body)

    def test_ws_page_has_all_four_balance_buttons(self):
        self.page.goto(self._url("simulator:ws"))
        self.assertIn("/ws/", self.page.url, f"WS page redirected to {self.page.url}")
        html = self.page.content()
        for btn_id in ("applyBalanceBtn", "applyFullBalanceBtn", "applyWindBalanceBtn", "applyWindFullBalanceBtn"):
            self.assertIn(f'id="{btn_id}"', html, f"missing #{btn_id} in rendered HTML")
