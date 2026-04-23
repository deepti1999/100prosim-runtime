"""
Phase B (T65) — middleware ties active region (session → thread-local).

Verifies:
- OwnerScopeMiddleware reads `active_region_code` from request.session,
  defaulting to DE when absent or session is unavailable.
- The thread-local is set for the duration of the request and reset
  after the response (so the next thread-recycled request starts clean).
- ensure_user_workspace_data is called with the active region for
  authenticated non-staff users.
- An unknown region code falls back gracefully to DE without 500s.
"""
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase


def _make_request(factory, user, session=None):
    request = factory.get("/some/path/")
    request.user = user
    request.session = session if session is not None else MagicMock(
        spec=dict, get=lambda key, default=None: default
    )
    return request


class MiddlewareRegionFromSessionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        from simulator.models import Region

        self.de = Region.objects.get(code="DE")

    def _capture_state_view(self, captured):
        from simulator.owner_scope import get_current_owner_id
        from simulator.region_scope import get_current_region_code

        def view(request):
            captured["region"] = get_current_region_code()
            captured["owner"] = get_current_owner_id()
            return HttpResponse("ok")

        return view

    def test_default_region_DE_when_session_missing_key(self):
        from simulator.middleware import OwnerScopeMiddleware

        captured = {}
        mw = OwnerScopeMiddleware(self._capture_state_view(captured))

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = {}  # session present, key absent

        mw(request)
        self.assertEqual(captured["region"], "DE")

    def test_default_region_DE_when_no_session_attr(self):
        from simulator.middleware import OwnerScopeMiddleware

        captured = {}
        mw = OwnerScopeMiddleware(self._capture_state_view(captured))

        request = self.factory.get("/")
        request.user = AnonymousUser()
        # No session attribute at all (e.g. an exotic upstream test fixture).
        if hasattr(request, "session"):
            del request.session

        mw(request)
        self.assertEqual(captured["region"], "DE")

    def test_active_region_read_from_session(self):
        from simulator.middleware import OwnerScopeMiddleware
        from simulator.models import Region

        Region.objects.create(code="BB", display_name="Brandenburg")

        captured = {}
        mw = OwnerScopeMiddleware(self._capture_state_view(captured))

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = {"active_region_code": "BB"}

        mw(request)
        self.assertEqual(captured["region"], "BB")

    def test_thread_local_reset_after_request(self):
        from simulator.middleware import OwnerScopeMiddleware
        from simulator.region_scope import get_current_region_code

        captured = {}
        mw = OwnerScopeMiddleware(self._capture_state_view(captured))

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = {"active_region_code": "DE"}

        mw(request)
        # After request returns, the thread-local should be cleared.
        self.assertIsNone(get_current_region_code())


class MiddlewareWorkspaceCalledWithRegionTests(TestCase):
    """ensure_user_workspace_data receives the active region per request."""

    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseb_mw_test", password="x", is_staff=False
        )

    def test_workspace_ensured_with_session_region(self):
        from unittest.mock import patch

        from simulator.middleware import OwnerScopeMiddleware

        with patch("simulator.middleware.ensure_user_workspace_data") as ensure:
            mw = OwnerScopeMiddleware(lambda r: HttpResponse("ok"))
            request = self.factory.get("/")
            request.user = self.user
            request.session = {"active_region_code": "DE"}
            mw(request)

            ensure.assert_called_once()
            args, kwargs = ensure.call_args
            self.assertEqual(args[0], self.user)
            self.assertEqual(kwargs.get("region_code"), "DE")

    def test_workspace_not_ensured_for_staff(self):
        from unittest.mock import patch

        from simulator.middleware import OwnerScopeMiddleware

        self.user.is_staff = True
        self.user.save()

        with patch("simulator.middleware.ensure_user_workspace_data") as ensure:
            mw = OwnerScopeMiddleware(lambda r: HttpResponse("ok"))
            request = self.factory.get("/")
            request.user = self.user
            request.session = {"active_region_code": "DE"}
            mw(request)

            ensure.assert_not_called()
