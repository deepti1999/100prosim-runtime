"""
Phase B (T65) — region-aware OwnerScopedManager + workspace_service.

Verifies:
- A `region_scope(code)` thread-local context manager exists, mirroring
  the existing owner_scope pattern.
- OwnerScopedManager.get_queryset() filters by region__code when the
  thread-local is set (and is a no-op when unset, preserving back-compat).
- ensure_user_workspace_data(user, region_code='DE') clones the
  region-scoped base rows into per-(owner, region) workspace rows.
- A user with both DE and BB workspaces sees no cross-region leakage:
  with region_scope('DE') only DE rows are visible; with 'BB' only BB.
- The cache key on OwnerScopedManager's owner-presence shortcut
  includes the region so switching region invalidates the per-region
  presence assumption.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase


class RegionScopeContextManagerTests(TestCase):
    """region_scope sets + resets a thread-local region code."""

    def test_module_importable(self):
        from simulator import region_scope as rs

        self.assertTrue(hasattr(rs, "region_scope"))
        self.assertTrue(hasattr(rs, "set_current_region"))
        self.assertTrue(hasattr(rs, "reset_current_region"))
        self.assertTrue(hasattr(rs, "get_current_region_code"))

    def test_region_scope_sets_and_resets(self):
        from simulator.region_scope import (
            get_current_region_code,
            region_scope,
            reset_current_region,
        )

        reset_current_region()
        self.assertIsNone(get_current_region_code())
        with region_scope("DE"):
            self.assertEqual(get_current_region_code(), "DE")
        self.assertIsNone(get_current_region_code())

    def test_nested_region_scope_restores_outer(self):
        from simulator.region_scope import (
            get_current_region_code,
            region_scope,
            reset_current_region,
        )

        reset_current_region()
        with region_scope("DE"):
            with region_scope("BB"):
                self.assertEqual(get_current_region_code(), "BB")
            self.assertEqual(get_current_region_code(), "DE")
        self.assertIsNone(get_current_region_code())


class OwnerScopedManagerRegionFilterTests(TestCase):
    """When the region thread-local is set, only rows of that region surface."""

    def setUp(self):
        from simulator.models import LandUse, Region

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg")
        LandUse.all_objects.create(code="LU_PB_DE", name="DE base", region=self.de)
        LandUse.all_objects.create(code="LU_PB_BB", name="BB base", region=self.bb)

    def test_no_region_context_returns_both(self):
        """Back-compat: without a region scope set, no region filter is applied."""
        from simulator.models import LandUse
        from simulator.region_scope import reset_current_region

        reset_current_region()
        codes = set(LandUse.objects.values_list("code", flat=True))
        self.assertIn("LU_PB_DE", codes)
        self.assertIn("LU_PB_BB", codes)

    def test_region_DE_returns_DE_only(self):
        from simulator.models import LandUse
        from simulator.region_scope import region_scope

        with region_scope("DE"):
            codes = set(LandUse.objects.values_list("code", flat=True))
            self.assertIn("LU_PB_DE", codes)
            self.assertNotIn("LU_PB_BB", codes)

    def test_region_BB_returns_BB_only(self):
        from simulator.models import LandUse
        from simulator.region_scope import region_scope

        with region_scope("BB"):
            codes = set(LandUse.objects.values_list("code", flat=True))
            self.assertIn("LU_PB_BB", codes)
            self.assertNotIn("LU_PB_DE", codes)


class WorkspaceServiceRegionAwareTests(TestCase):
    """ensure_user_workspace_data clones the region-scoped overlay only."""

    def setUp(self):
        from simulator.models import LandUse, Region, RenewableData, VerbrauchData

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg")
        # Two distinct base rows per model per region so the clone-count proof is unambiguous.
        for r, suffix in ((self.de, "DE"), (self.bb, "BB")):
            LandUse.all_objects.create(code=f"LU_BASE_{suffix}", name=f"{suffix} base", region=r)
            RenewableData.all_objects.create(
                category="ZZ", name=f"{suffix} base", unit="GWh", code=f"R_BASE_{suffix}", region=r,
            )
            VerbrauchData.all_objects.create(
                code=f"V_BASE_{suffix}", category=f"{suffix} base", unit="GWh", region=r,
            )

        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseb_workspace_user", password="x", is_staff=False
        )

    def test_ensure_workspace_clones_DE_overlay(self):
        from simulator.models import LandUse
        from simulator.workspace_service import ensure_user_workspace_data

        ensure_user_workspace_data(self.user, region_code="DE")
        de_rows = LandUse.all_objects.filter(owner=self.user, region=self.de)
        self.assertGreater(de_rows.count(), 0, "No workspace rows cloned for DE")
        cloned_codes = set(de_rows.values_list("code", flat=True))
        self.assertIn("LU_BASE_DE", cloned_codes)
        # Must not pull BB rows into DE workspace.
        self.assertNotIn("LU_BASE_BB", cloned_codes)

    def test_ensure_workspace_clones_BB_separately(self):
        from simulator.models import LandUse
        from simulator.workspace_service import ensure_user_workspace_data

        ensure_user_workspace_data(self.user, region_code="DE")
        ensure_user_workspace_data(self.user, region_code="BB")

        bb_rows = LandUse.all_objects.filter(owner=self.user, region=self.bb)
        de_rows = LandUse.all_objects.filter(owner=self.user, region=self.de)
        self.assertGreater(de_rows.count(), 0)
        self.assertGreater(bb_rows.count(), 0)
        self.assertNotIn("LU_BASE_BB", set(de_rows.values_list("code", flat=True)))
        self.assertNotIn("LU_BASE_DE", set(bb_rows.values_list("code", flat=True)))


class NoCrossRegionLeakageTests(TestCase):
    """The combined (owner, region) scope yields zero cross-region rows."""

    def setUp(self):
        from simulator.models import LandUse, Region

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg")
        for r, suffix in ((self.de, "DE"), (self.bb, "BB")):
            LandUse.all_objects.create(code=f"LU_BASE_{suffix}", name=f"{suffix} base", region=r)

        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseb_leakage_user", password="x", is_staff=False
        )
        from simulator.workspace_service import ensure_user_workspace_data

        ensure_user_workspace_data(self.user, region_code="DE")
        ensure_user_workspace_data(self.user, region_code="BB")

    def test_user_with_both_regions_sees_DE_only_under_DE_scope(self):
        from simulator.models import LandUse
        from simulator.owner_scope import owner_scope
        from simulator.region_scope import region_scope

        with region_scope("DE"), owner_scope(self.user):
            codes = set(LandUse.objects.values_list("code", flat=True))
        self.assertIn("LU_BASE_DE", codes)
        self.assertNotIn("LU_BASE_BB", codes)

    def test_user_with_both_regions_sees_BB_only_under_BB_scope(self):
        from simulator.models import LandUse
        from simulator.owner_scope import owner_scope
        from simulator.region_scope import region_scope

        with region_scope("BB"), owner_scope(self.user):
            codes = set(LandUse.objects.values_list("code", flat=True))
        self.assertIn("LU_BASE_BB", codes)
        self.assertNotIn("LU_BASE_DE", codes)

    def test_owner_presence_cache_keyed_per_region(self):
        """Switching region must NOT carry over the previous region's
        owner-presence answer (else a workspace-existing-for-DE answer
        would mask BB's separate workspace).
        """
        from simulator.models import LandUse
        from simulator.owner_scope import owner_scope
        from simulator.region_scope import region_scope

        with region_scope("DE"), owner_scope(self.user):
            de_count = LandUse.objects.filter(code__startswith="LU_BASE_").count()
        with region_scope("BB"), owner_scope(self.user):
            bb_count = LandUse.objects.filter(code__startswith="LU_BASE_").count()
        self.assertEqual(de_count, 1)
        self.assertEqual(bb_count, 1)
