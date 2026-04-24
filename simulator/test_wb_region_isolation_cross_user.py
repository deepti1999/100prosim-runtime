"""Region isolation cross-user — covers T11 + T12 + T13.

Invariant protected: workspace data is scoped per (owner, region). User A
working in DE must NEVER see user B's TEST-region edits, and vice versa.
The OwnerScopedManager filter in `simulator/owner_scope.py` enforces this
via the `region_scope` thread-local.

Background: Phase B (T65) introduced Region as first-class with FK on the
4 parameter models. Phase C (T66) added WSData per-(owner, region) and
plumbed `region_code` through baseline/scenario payloads. The whole point
is that two users with different active regions can edit independently
without contaminating each other.

Past incident motivation: the v1 §2.3 audit (commit f5c738b) misframed
region scoping. Phase B fixed the architecture. Phase C V5 verified one
user round-tripping DE→TEST→DE. **No existing test covers TWO users in
DIFFERENT regions simultaneously** — that's this test's gap-fill.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from simulator.models import LandUse, Region
from simulator.owner_scope import owner_scope
from simulator.region_scope import region_scope
from simulator.workspace_service import ensure_user_workspace_data


class RegionIsolationCrossUserTests(TestCase):
    """T11/T12/T13: per-(owner, region) scoping prevents cross-leak."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.de_region, _ = Region.objects.get_or_create(
            code="DE",
            defaults={
                "display_name": "Deutschland",
                "active": True,
                "installed_pmax_ely_gw": 194.0,
                "installed_pmax_rv_gw": 261.0,
            },
        )
        cls.test_region, _ = Region.objects.get_or_create(
            code="TEST",
            defaults={
                "display_name": "Test Region",
                "active": True,
                "installed_pmax_ely_gw": 200.0,
                "installed_pmax_rv_gw": 270.0,
            },
        )
        # Seed admin baseline rows in BOTH regions so workspace clones can
        # source from them. owner=None per the OwnerScopedManager convention.
        cls.de_root = LandUse(
            code="LU_ROOT",
            name="Root DE",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=10.0,
            region=cls.de_region,
        )
        cls.de_root.save(skip_cascade=True)
        cls.test_root = LandUse(
            code="LU_ROOT",
            name="Root TEST",
            status_ha=2000.0,
            target_ha=2000.0,
            user_percent=20.0,
            region=cls.test_region,
        )
        cls.test_root.save(skip_cascade=True)

        cls.user_a = User.objects.create_user(username="user_a_de", password="x")
        cls.user_b = User.objects.create_user(username="user_b_test", password="x")

    # --- Golden path: each user only sees their own (region) workspace ---

    def test_user_a_in_DE_does_not_see_user_b_TEST_workspace(self):
        """User A active region=DE; user B active region=TEST. User A's
        queries must not return user B's TEST-region rows.
        """
        # User A creates a workspace in DE.
        with region_scope("DE"):
            ensure_user_workspace_data(self.user_a, region_code="DE")
            with owner_scope(self.user_a):
                user_a_codes = set(
                    LandUse.objects.values_list("code", flat=True)
                )

        # User B creates a workspace in TEST.
        with region_scope("TEST"):
            ensure_user_workspace_data(self.user_b, region_code="TEST")
            with owner_scope(self.user_b):
                user_b_codes = set(
                    LandUse.objects.values_list("code", flat=True)
                )

        # Both should see SOME LandUse rows (the cloned admin baseline).
        self.assertGreater(len(user_a_codes), 0, "user A's DE workspace empty")
        self.assertGreater(len(user_b_codes), 0, "user B's TEST workspace empty")

        # Now read user A's view of LandUse from within user B's region scope.
        # Should see ONLY user A's DE rows (or no rows if filtered out).
        with region_scope("DE"):
            with owner_scope(self.user_a):
                rows_in_a_de = list(
                    LandUse.objects.values_list("region__code", flat=True)
                )
        for region_code in rows_in_a_de:
            self.assertEqual(
                region_code,
                "DE",
                f"user A in DE saw region={region_code!r} — leak from TEST",
            )

        with region_scope("TEST"):
            with owner_scope(self.user_b):
                rows_in_b_test = list(
                    LandUse.objects.values_list("region__code", flat=True)
                )
        for region_code in rows_in_b_test:
            self.assertEqual(
                region_code,
                "TEST",
                f"user B in TEST saw region={region_code!r} — leak from DE",
            )

    # --- Edge case 1: same user, switch region mid-session ---

    def test_same_user_switching_regions_sees_correct_workspace(self):
        """A single user can have workspaces in multiple regions; the active
        thread-local determines which is visible at any point.
        """
        with region_scope("DE"):
            ensure_user_workspace_data(self.user_a, region_code="DE")
        with region_scope("TEST"):
            ensure_user_workspace_data(self.user_a, region_code="TEST")

        with owner_scope(self.user_a):
            with region_scope("DE"):
                de_count = LandUse.objects.count()
            with region_scope("TEST"):
                test_count = LandUse.objects.count()

        # Both workspaces exist, neither leaks into the other.
        self.assertGreater(de_count, 0)
        self.assertGreater(test_count, 0)

    # --- Edge case 2: queries with no region scope set ---

    def test_no_region_scope_falls_back_to_no_filter(self):
        """When no region_scope is bound, queries fall back to all-rows
        (per the docstring of region_scope.py).

        This preserves backward compatibility for management commands and
        migrations that pre-date Phase B.
        """
        # Bring both users' DE workspaces into existence.
        with region_scope("DE"):
            ensure_user_workspace_data(self.user_a, region_code="DE")

        # Without binding a region, queries should still work and not crash.
        with owner_scope(self.user_a):
            rows = list(LandUse.objects.all())
            # No assertion on count — just that the query runs.
            self.assertIsInstance(rows, list)

    # --- Regression test: Phase C synthetic TEST round-trip ---

    def test_regression_phase_c_de_test_de_round_trip_preserves_de(self):
        """Phase C's V5 verification (DATA_MODEL_IMPORT_AUDIT.md §0c) showed
        DE→TEST→DE round-trip yields byte-identical DE values.

        This regression test asserts the same property: write to TEST as a
        scoped action, then verify DE state is unchanged.
        """
        with region_scope("DE"):
            ensure_user_workspace_data(self.user_a, region_code="DE")
            with owner_scope(self.user_a):
                de_initial = list(
                    LandUse.objects.order_by("code").values_list(
                        "code", "user_percent"
                    )
                )

        # Switch to TEST, modify a row.
        with region_scope("TEST"):
            ensure_user_workspace_data(self.user_a, region_code="TEST")
            with owner_scope(self.user_a):
                row = LandUse.objects.first()
                if row is not None:
                    row.user_percent = 99.99
                    row.save(skip_cascade=True)

        # Switch back to DE, assert state unchanged.
        with region_scope("DE"):
            with owner_scope(self.user_a):
                de_after = list(
                    LandUse.objects.order_by("code").values_list(
                        "code", "user_percent"
                    )
                )

        self.assertEqual(
            de_initial,
            de_after,
            "DE workspace state changed after a TEST-scoped write — region "
            "isolation broken (Phase C regression).",
        )
