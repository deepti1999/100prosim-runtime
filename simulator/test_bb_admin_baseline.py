"""Phase 4-B tests — T16, T17, T18: admin-provided shared baseline.

Per PDF §2.4.2, there is exactly one shared admin baseline. Regular users
cannot create or overwrite it; they can only reset their workspace to it.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import BaselineSnapshot, LandUse


class AdminBaselineContractTests(TestCase):
    """Exercises the T16/T17/T18 contract directly against the endpoints."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="bb_admin", password="x", is_staff=True
        )
        cls.user = User.objects.create_user(
            username="bb_user", password="x", is_staff=False
        )

        # Shared (owner=None) rows that form the "admin baseline scope".
        cls.root = LandUse(
            code="LU_ROOT",
            name="Root",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=None,
        )
        cls.root.save(skip_cascade=True)
        cls.child = LandUse(
            code="LU_2.1",
            name="Solar Land",
            status_ha=100.0,
            target_ha=100.0,
            user_percent=7.0,
            increase_limit_baseline_percent=10.0,
            parent=cls.root,
        )
        cls.child.save(skip_cascade=True)

    def test_non_staff_cannot_create_baseline(self):
        """T16: 'Baseline erstellen' is admin-only."""
        self.client.force_login(self.user)
        response = self.client.post(reverse("simulator:create_baseline"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(BaselineSnapshot.objects.count(), 0)

    def test_admin_creates_shared_baseline(self):
        """T18: admin baseline stored once, keyed as 'global', owner=None."""
        self.client.force_login(self.admin)
        response = self.client.post(reverse("simulator:create_baseline"))
        self.assertEqual(response.status_code, 200)
        snapshots = BaselineSnapshot.objects.all()
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].key, "global")
        self.assertIsNone(snapshots[0].owner)

    def test_non_staff_can_restore_from_admin_baseline(self):
        """T17 + T18: user resets to the admin baseline, seeing admin's
        7% LU_2.1 even though they may have mutated things.
        """
        self.client.force_login(self.admin)
        self.client.post(reverse("simulator:create_baseline"))

        # Admin's captured baseline has LU_2.1 user_percent=7.0.
        # Now the admin mutates it.
        landuse = LandUse.objects.get(code="LU_2.1")
        landuse.user_percent = 42.0
        landuse.save(skip_cascade=True)

        # Regular user hits Reset to Baseline.
        self.client.logout()
        self.client.force_login(self.user)
        response = self.client.post(reverse("simulator:restore_baseline"))
        self.assertEqual(response.status_code, 200)

        # User's workspace now has LU_2.1 at 7% (the admin-captured value),
        # independent of the admin's current state.
        # Because the restore targets the user's workspace scope, there is
        # a user-scoped LU_2.1 row with the baseline value.
        user_copies = LandUse.all_objects.filter(owner=self.user, code="LU_2.1")
        self.assertTrue(user_copies.exists())
        self.assertAlmostEqual(user_copies.first().user_percent, 7.0)

    def test_restore_without_baseline_returns_404(self):
        """No baseline yet -> user-friendly error, not a crash."""
        self.client.force_login(self.user)
        BaselineSnapshot.objects.all().delete()
        response = self.client.post(reverse("simulator:restore_baseline"))
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertIn("Baseline", payload["error"])

    def test_baseline_info_exposes_can_create_flag(self):
        """UI uses can_create to decide whether to show 'Baseline erstellen'."""
        self.client.force_login(self.admin)
        admin_info = self.client.get(reverse("simulator:get_baseline_info")).json()
        self.assertTrue(admin_info["can_create"])

        self.client.logout()
        self.client.force_login(self.user)
        user_info = self.client.get(reverse("simulator:get_baseline_info")).json()
        self.assertFalse(user_info["can_create"])
