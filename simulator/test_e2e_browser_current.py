"""Real-browser Selenium smoke tests for the current app's stable UI flows."""

from unittest import SkipTest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

try:
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except Exception:  # pragma: no cover - import availability is environment-specific
    webdriver = None
    WebDriverException = Exception
    By = None
    EC = None
    WebDriverWait = None

class BrowserCurrentAppSmokeTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            super().setUpClass()
        except PermissionError as exc:
            raise SkipTest(f"Live browser test server could not start in this environment: {exc}") from exc
        if webdriver is None:
            raise SkipTest("Selenium is not installed in this environment.")

        # Try available drivers in order: Chrome headless (cross-platform, Selenium
        # Manager auto-installs chromedriver), then Firefox, then Safari (macOS only).
        last_err = None
        for factory in (cls._try_chrome, cls._try_firefox, cls._try_safari):
            try:
                cls.driver = factory()
                break
            except WebDriverException as exc:
                last_err = exc
                continue
            except Exception as exc:
                last_err = exc
                continue
        else:
            raise SkipTest(f"No WebDriver available (tried Chrome, Firefox, Safari): {last_err}")

        cls.driver.set_window_size(1440, 1100)
        cls.wait = WebDriverWait(cls.driver, 15)

    @staticmethod
    def _try_chrome():
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=opts)

    @staticmethod
    def _try_firefox():
        from selenium.webdriver.firefox.options import Options
        opts = Options()
        opts.add_argument("--headless")
        return webdriver.Firefox(options=opts)

    @staticmethod
    def _try_safari():
        return webdriver.Safari()

    @classmethod
    def tearDownClass(cls):
        driver = getattr(cls, "driver", None)
        if driver is not None:
            driver.quit()
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        # Note: setUpTestData runs per-class for TestCase. LiveServerTestCase is a
        # TransactionTestCase, whose DB is flushed between test methods, so the
        # user is re-created in setUp rather than relying on TestCase semantics.
        pass

    def setUp(self):
        super().setUp()
        # Load seed so views that touch VerbrauchData / WS365 don't 500.
        from simulator._e2e_seed_helper import load_e2e_seed
        load_e2e_seed()
        u, _ = get_user_model().objects.get_or_create(
            username="browser_smoke_user",
        )
        u.set_password("browser-pass-123")
        u.is_active = True
        u.save()
        self.user = u

    def _url(self, name):
        return f"{self.live_server_url}{reverse(name)}"

    def _login(self):
        self.driver.get(self._url("simulator:login"))
        self.wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(
            "browser_smoke_user"
        )
        self.driver.find_element(By.NAME, "password").send_keys("browser-pass-123")
        self.driver.find_element(By.CSS_SELECTOR, "button.btn-login").click()
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'Simulations-Übersicht')]"))
        )

    def test_login_opens_dashboard_with_current_sidebar_entries(self):
        self._login()

        self.assertIn("/simulation/", self.driver.current_url)
        page_text = self.driver.find_element(By.TAG_NAME, "body").text

        for label in (
            "Simulations-Übersicht",
            "Flächennutzung",
            "Erneuerbare Energien",
            "Verbrauch",
            "Szenario-Abgleich",
            "Cockpit",
            "Jahresstrom",
            "Bilanz",
            "Benutzerhandbuch",
        ):
            self.assertIn(label, page_text)

    def test_scenario_comparison_page_shows_current_controls_in_browser(self):
        self._login()

        self.driver.find_element(By.LINK_TEXT, "Szenario-Abgleich").click()
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'Szenario-Abgleich')]"))
        )

        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        for label in (
            "WS Balance Solar",
            "Sector + WS Solar Balance",
            "WS Balance Wind",
            "Sector + WS Wind Balance",
            "Jahresstrom-Hinweis",
            "Zur Seite Jahresstrom",
        ):
            self.assertIn(label, page_text)
        # Stakeholder T19/T20 (PDF §2.4.3): "Goal Seek" and "Aktualisieren"
        # buttons removed — goal-seek runs automatically on page load.
        for removed_label in ("Goal Seek ausführen", "Aktualisieren"):
            self.assertNotIn(removed_label, page_text)

    def test_user_manual_is_reachable_from_sidebar_in_browser(self):
        self._login()

        self.driver.find_element(By.LINK_TEXT, "Benutzerhandbuch").click()
        # The template uses <h2> for the manual heading, not <h1>.
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(., 'User Manual')]"))
        )

        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn("Step 11", page_text)
        self.assertIn("Scenarios", page_text)
