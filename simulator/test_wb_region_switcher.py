"""
Phase B (T65) — region switcher view + nav dropdown.

Verifies:
- POST /api/region/set/ persists region_code in session for valid codes.
- Invalid / inactive / empty region_code is rejected.
- GET method on the switcher endpoint is rejected.
- A region context processor exposes active regions + active code to
  every template (so the dropdown can render anywhere base.html is used).
- The nav dropdown renders for authenticated users with at least one
  active region present and lists only active regions.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RegionSwitcherViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="region_switcher_user", password="phaseb!", is_staff=False
        )
        self.client.login(username="region_switcher_user", password="phaseb!")

    def test_post_valid_region_persists_in_session(self):
        url = reverse("simulator:set_active_region")
        resp = self.client.post(url, {"region_code": "DE"}, HTTP_REFERER="/landuse/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.session.get("active_region_code"), "DE")

    def test_post_invalid_region_rejected(self):
        url = reverse("simulator:set_active_region")
        resp = self.client.post(url, {"region_code": "XX_NOT_REAL"}, HTTP_REFERER="/landuse/")
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(self.client.session.get("active_region_code"), "XX_NOT_REAL")

    def test_post_inactive_region_rejected(self):
        from simulator.models import Region

        Region.objects.create(code="ZZ_INACTIVE", display_name="Inactive Test", active=False)
        url = reverse("simulator:set_active_region")
        resp = self.client.post(url, {"region_code": "ZZ_INACTIVE"}, HTTP_REFERER="/landuse/")
        self.assertEqual(resp.status_code, 400)

    def test_post_empty_region_rejected(self):
        url = reverse("simulator:set_active_region")
        resp = self.client.post(url, {"region_code": ""}, HTTP_REFERER="/landuse/")
        self.assertEqual(resp.status_code, 400)

    def test_get_method_not_allowed(self):
        url = reverse("simulator:set_active_region")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)

    def test_anonymous_user_redirected(self):
        self.client.logout()
        url = reverse("simulator:set_active_region")
        resp = self.client.post(url, {"region_code": "DE"})
        # login_required redirects to LOGIN_URL
        self.assertIn(resp.status_code, (302, 401, 403))


class RegionContextProcessorTests(TestCase):
    """The context processor exposes active_regions + active_region_code."""

    def test_processor_module_importable(self):
        from simulator import context_processors

        self.assertTrue(hasattr(context_processors, "region_context"))

    def test_active_regions_filters_inactive(self):
        from simulator.context_processors import region_context
        from simulator.models import Region

        Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        Region.objects.create(code="ZZ", display_name="Inactive", active=False)

        from django.test import RequestFactory

        request = RequestFactory().get("/")
        ctx = region_context(request)
        codes = [r.code for r in ctx["active_regions"]]
        self.assertIn("DE", codes)
        self.assertIn("BB", codes)
        self.assertNotIn("ZZ", codes)

    def test_active_region_code_default_DE(self):
        from simulator.context_processors import region_context
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        ctx = region_context(request)
        self.assertEqual(ctx["active_region_code"], "DE")


class RegionDropdownRenderingTests(TestCase):
    """The dropdown surfaces in base.html for authenticated users."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="dropdown_user", password="phaseb!", is_staff=False
        )
        self.client.login(username="dropdown_user", password="phaseb!")

    def test_dropdown_marker_visible_on_main_page(self):
        # The dropdown is rendered in base.html — landuse_list extends it.
        url = reverse("simulator:landuse_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "data-region-switcher")

    def test_dropdown_lists_DE(self):
        url = reverse("simulator:landuse_list")
        resp = self.client.get(url)
        self.assertContains(resp, "Deutschland")

    def test_dropdown_hidden_for_anonymous_user(self):
        self.client.logout()
        url = reverse("simulator:landing_page")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "data-region-switcher")
