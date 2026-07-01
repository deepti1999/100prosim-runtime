"""
Phase C (T66) — WSData per-(owner, region) scoping.

Phase B left WSData per-user-only. Phase C adds region scope so a user
who switches from DE to BB sees BB's 365-day timeseries instead of
their DE one.

Decision rationale (per project runtime notes "Architectural rule"):
- WSData is *workspace state* (the 365-day simulation result), not
  just parameter substrate. It depends on parameters that are now
  region-scoped (Phase B), so WSData must be region-scoped too —
  otherwise a BB user reads DE timeseries derived from DE parameters.
- OwnerScopedManager already filters by region (Phase B step 3) when
  the model has a region field; adding the FK plumbs scoping
  automatically with no extra query changes.
- Per-(owner, region) — not per-region only — because the user can
  edit their workspace WSData independently of the base; same shape
  as LandUse/Renewable/Verbrauch.
"""
from django.contrib.auth import get_user_model
from django.db import models as django_models
from django.test import TestCase


class WSDataRegionFKPresenceTests(TestCase):
    def test_wsdata_has_region_fk(self):
        from simulator.models import Region
        from simulator.ws_models import WSData

        field = WSData._meta.get_field("region")
        self.assertIsInstance(field, django_models.ForeignKey)
        self.assertIs(field.related_model, Region)
        self.assertIs(
            field.remote_field.on_delete,
            django_models.PROTECT,
            "WSData.region must use PROTECT (same convention as parameter models).",
        )

    def test_wsdata_create_defaults_DE(self):
        from simulator.ws_models import WSData

        row = WSData.all_objects.create(tag_im_jahr=999, solar_promille=0.5)
        self.assertEqual(row.region.code, "DE")

    def test_wsdata_unique_constraint_includes_region(self):
        from simulator.ws_models import WSData

        constraint_field_sets = [
            set(c.fields)
            for c in WSData._meta.constraints
            if hasattr(c, "fields") and c.fields
        ]
        self.assertIn(
            {"owner", "region", "tag_im_jahr"},
            constraint_field_sets,
            "WSData needs UniqueConstraint(['owner','region','tag_im_jahr']) so "
            "the same day can repeat across regions per workspace.",
        )


class WSDataRegionScopingTests(TestCase):
    """Querying WSData with a region context returns only that region's rows."""

    def setUp(self):
        from simulator.models import Region
        from simulator.ws_models import WSData

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        WSData.all_objects.create(tag_im_jahr=1, solar_promille=0.5, region=self.de)
        WSData.all_objects.create(tag_im_jahr=1, solar_promille=0.9, region=self.bb)

    def test_no_region_context_returns_both(self):
        from simulator.region_scope import reset_current_region
        from simulator.ws_models import WSData

        reset_current_region()
        rows = WSData.objects.filter(tag_im_jahr=1)
        self.assertEqual(rows.count(), 2)

    def test_region_DE_returns_DE_only(self):
        from simulator.region_scope import region_scope
        from simulator.ws_models import WSData

        with region_scope("DE"):
            rows = list(WSData.objects.filter(tag_im_jahr=1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].solar_promille, 0.5)

    def test_region_BB_returns_BB_only(self):
        from simulator.region_scope import region_scope
        from simulator.ws_models import WSData

        with region_scope("BB"):
            rows = list(WSData.objects.filter(tag_im_jahr=1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].solar_promille, 0.9)


class WSDataWorkspaceClonePerRegionTests(TestCase):
    def setUp(self):
        from simulator.models import Region
        from simulator.ws_models import WSData

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        # 3-day base for each region (cheap)
        for day in range(1, 4):
            WSData.all_objects.create(
                tag_im_jahr=day, solar_promille=0.5 * day, region=self.de
            )
            WSData.all_objects.create(
                tag_im_jahr=day, solar_promille=0.9 * day, region=self.bb
            )
        User = get_user_model()
        self.user = User.objects.create_user(
            username="phaseC_ws_user", password="x", is_staff=False
        )

    def test_workspace_clone_creates_DE_ws_rows(self):
        from simulator.workspace_service import ensure_user_workspace_data
        from simulator.ws_models import WSData

        ensure_user_workspace_data(self.user, region_code="DE")
        de_rows = WSData.all_objects.filter(owner=self.user, region=self.de)
        self.assertEqual(de_rows.count(), 3)

    def test_workspace_clone_creates_BB_ws_rows_separately(self):
        from simulator.workspace_service import ensure_user_workspace_data
        from simulator.ws_models import WSData

        ensure_user_workspace_data(self.user, region_code="DE")
        ensure_user_workspace_data(self.user, region_code="BB")
        de_rows = WSData.all_objects.filter(owner=self.user, region=self.de)
        bb_rows = WSData.all_objects.filter(owner=self.user, region=self.bb)
        self.assertEqual(de_rows.count(), 3)
        self.assertEqual(bb_rows.count(), 3)
        # The BB clone should have BB's source values, not DE's.
        bb_solar = sorted(bb_rows.values_list("solar_promille", flat=True))
        self.assertEqual(bb_solar, [0.9, 1.8, 2.7])
