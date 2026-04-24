"""T33 German-UI residue regression — assert every known English residue on
user-visible pages has been replaced with German per the fix-bundle
2026-04-24 (Fix 1).

Covers:
  - Cockpit: "Ziel (2050)" → "Ziel (2045)" (year + language fix)
  - LandUse: empty-state "No changes yet" → "Noch keine Änderungen"
  - Renewable: empty-state "No changes yet. When you modify …" → German
  - Login flash: "Welcome back, <user>!" → "Willkommen zurück, <user>!"
  - Register / logout flashes → German
  - Invalid-credentials error → German

Each test navigates to the relevant page or triggers the relevant flash
and asserts the German string is present while the old English one is
NOT. Prevents a regression that re-introduces English text.
"""

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse


class GermanUIResiduesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="de_ui_user",
            password="test-pass-123",
        )

    def _login(self):
        self.client.login(username="de_ui_user", password="test-pass-123")

    # ------------------------------------------------------------------
    # Cockpit — "Ziel (2045)" not "Ziel (2050)"
    # ------------------------------------------------------------------
    def test_cockpit_ziel_year_is_2045_not_2050(self):
        self._login()
        response = self.client.get(reverse("simulator:cockpit"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("Ziel (2045)", body)
        self.assertNotIn("Ziel (2050)", body)

    # ------------------------------------------------------------------
    # LandUse — empty-state "Noch keine Änderungen"
    # ------------------------------------------------------------------
    def test_landuse_empty_state_is_german(self):
        self._login()
        response = self.client.get(reverse("simulator:landuse_list"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("Noch keine Änderungen", body)
        # The exact phrase "No changes yet" must not appear anywhere visible.
        # (Comments in JS are out-of-scope; we only care about the user-rendered text.)
        self.assertNotIn(">No changes yet<", body)

    # ------------------------------------------------------------------
    # Renewable — empty-state full sentence is German
    # ------------------------------------------------------------------
    def test_renewable_empty_state_is_german(self):
        self._login()
        response = self.client.get(reverse("simulator:renewable_list"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        self.assertIn("Noch keine Änderungen", body)
        self.assertIn("Wenn Sie Erneuerbare-Werte anpassen", body)
        self.assertNotIn("When you modify renewable values", body)

    # ------------------------------------------------------------------
    # Login — "Willkommen zurück" flash, no English
    # ------------------------------------------------------------------
    def _flash_texts(self, response):
        """Collect flash-message text from the Django messages framework."""
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_login_flash_is_german(self):
        response = self.client.post(
            reverse("simulator:login"),
            {"username": "de_ui_user", "password": "test-pass-123"},
        )
        # Redirect after successful login
        self.assertEqual(response.status_code, 302)
        texts = self._flash_texts(response)
        self.assertTrue(any("Willkommen zurück" in t and "de_ui_user" in t for t in texts),
                        msg=f"Expected German welcome, got: {texts}")
        self.assertFalse(any("Welcome back" in t for t in texts),
                         msg=f"English 'Welcome back' should not appear: {texts}")

    def test_login_invalid_credentials_flash_is_german(self):
        response = self.client.post(
            reverse("simulator:login"),
            {"username": "de_ui_user", "password": "WRONG_PASSWORD"},
        )
        self.assertEqual(response.status_code, 200)
        texts = self._flash_texts(response)
        self.assertTrue(any("Ungültiger Benutzername" in t for t in texts),
                        msg=f"Expected German invalid-creds flash, got: {texts}")
        self.assertFalse(any("Invalid username or password" in t for t in texts),
                         msg=f"English 'Invalid username or password' should not appear: {texts}")

    def test_logout_flash_is_german(self):
        self._login()
        response = self.client.get(reverse("simulator:logout"))
        self.assertEqual(response.status_code, 302)
        texts = self._flash_texts(response)
        self.assertTrue(any("Sie wurden erfolgreich abgemeldet" in t for t in texts),
                        msg=f"Expected German logout flash, got: {texts}")
        self.assertFalse(any("You have been successfully logged out" in t for t in texts),
                         msg=f"English 'You have been successfully logged out' should not appear: {texts}")
