"""
Phase C (T66) — scenario / baseline snapshot payload carries region_code.

Phase B excluded the `region` FK from the per-row serialized payload to
unblock JSON serialization. Phase C adds a top-level `region_code` key so
restored rows go back to the right region instead of always defaulting
to DE.

Back-compat: snapshots saved before this flip have no region_code key;
restore falls back to DE (the only region that existed pre-Phase-C).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase


class SnapshotPayloadCarriesRegionTests(TestCase):
    """`_snapshot_payload_for_owner` writes region_code in the payload."""

    def setUp(self):
        from simulator.models import LandUse, Region

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        # One DE base row + one BB base row so payload has something to serialize.
        LandUse.all_objects.create(
            code="LU_PCS_DE", name="DE row", status_ha=10.0, region=self.de
        )
        LandUse.all_objects.create(
            code="LU_PCS_BB", name="BB row", status_ha=20.0, region=self.bb
        )

    def test_payload_contains_top_level_region_code(self):
        from simulator.baseline_api import _snapshot_payload_for_owner
        from simulator.region_scope import region_scope

        with region_scope("DE"):
            payload = _snapshot_payload_for_owner(None)
        self.assertIn(
            "region_code",
            payload,
            "Snapshot payload must include top-level region_code so restore "
            "can re-bind rows to the saved region.",
        )
        self.assertEqual(payload["region_code"], "DE")

    def test_payload_region_code_reflects_active_region(self):
        from simulator.baseline_api import _snapshot_payload_for_owner
        from simulator.region_scope import region_scope

        with region_scope("BB"):
            payload = _snapshot_payload_for_owner(None)
        self.assertEqual(payload["region_code"], "BB")


class SnapshotRestoreRegionRoundtripTests(TestCase):
    """Restoring a scenario binds rows back to the saved region."""

    def setUp(self):
        from simulator.models import LandUse, Region

        self.de = Region.objects.get(code="DE")
        self.bb = Region.objects.create(code="BB", display_name="Brandenburg", active=True)
        LandUse.all_objects.create(
            code="LU_RT_DE", name="DE base", status_ha=100.0, region=self.de
        )
        LandUse.all_objects.create(
            code="LU_RT_BB", name="BB base", status_ha=200.0, region=self.bb
        )
        User = get_user_model()
        self.user = User.objects.create_user(username="phaseC_rt_user", password="x")

    def test_round_trip_keeps_DE_rows_in_DE(self):
        from simulator.baseline_api import (
            _restore_snapshot_payload,
            _snapshot_payload_for_owner,
        )
        from simulator.models import LandUse
        from simulator.region_scope import region_scope

        with region_scope("DE"):
            payload = _snapshot_payload_for_owner(self.user)
        # Wipe the user's DE rows then restore.
        LandUse.all_objects.filter(owner=self.user, region=self.de).delete()
        with region_scope("DE"):
            _restore_snapshot_payload(self.user, payload)
        # The user should have NO BB-region rows from the DE snapshot restore.
        bb_count = LandUse.all_objects.filter(owner=self.user, region=self.bb).count()
        self.assertEqual(bb_count, 0, "DE snapshot must not create BB user rows")

    def test_legacy_payload_without_region_code_defaults_DE(self):
        """Snapshots saved before Phase C have no region_code key."""
        from simulator.baseline_api import _restore_snapshot_payload
        from simulator.models import LandUse

        legacy_payload = {
            "landuse": [
                {
                    "code": "LU_LEGACY",
                    "name": "legacy row",
                    "status_ha": 1.0,
                    "target_ha": None,
                    "status_formula_key": None,
                    "target_formula_key": None,
                    "user_percent": None,
                    "increase_limit_baseline_percent": None,
                    "target_locked": False,
                    "quelle": None,
                    "parent_code": None,
                }
            ],
            "renewable": [],
            "verbrauch": [],
            "ws": [],
        }
        _restore_snapshot_payload(self.user, legacy_payload)
        de_rows = LandUse.all_objects.filter(owner=self.user, region=self.de)
        self.assertEqual(
            de_rows.filter(code="LU_LEGACY").count(),
            1,
            "Legacy payload (no region_code) must restore to DE for back-compat.",
        )
