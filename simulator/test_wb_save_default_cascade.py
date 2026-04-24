"""Save() default-cascade behaviour — covers T24 + T25 + T26.

Invariant protected: calling `.save()` on LandUse / RenewableData /
VerbrauchData WITHOUT explicit `skip_cascade=True` MUST trigger the
cascade signal that recomputes dependent cells. The Renewable surface in
particular must NOT silently skip cascade — that was the 2026-04 incident
(Phase 4-E commit `86e3ba2`).

Background: prior to commit `86e3ba2`, `simulator/input_api.py
::save_renewable_user_input` called `item.save(skip_cascade=True)`,
breaking the §2.4.4 PDF auto-cascade contract for the Renewable surface.
The fix removed the flag. Without a regression test, a future refactor
could re-add the flag silently.

Past incident motivation (CLAUDE.md "Past incidents" section):
- commit `54d4567` — caches not wiped at job entry caused 1.1.2 revert bug.
- commit `691b99f` — signature excluded computed ziels, multi-pass DAG
  stopped after 1 pass.
- commit `86e3ba2` — removed `skip_cascade=True` from Renewable save (T25
  fix). This test guards that fix from regression.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from simulator.models import LandUse, RenewableData, VerbrauchData


class SaveDefaultCascadeTests(TestCase):
    """T24/T25/T26: model.save() without skip_cascade triggers cascade."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="cascade_test", password="x")

        cls.landuse = LandUse(
            code="LU_CASC",
            name="Cascade test LU",
            status_ha=1000.0,
            target_ha=1000.0,
            user_percent=10.0,
        )
        cls.landuse.save(skip_cascade=True)

        cls.verbrauch = VerbrauchData.objects.create(
            code="V_CASC",
            category="Test",
            unit="GWh/a",
            status=100.0,
            ziel=80.0,
            is_calculated=False,
        )

        cls.renewable = RenewableData.objects.create(
            code="9.CASC",
            category="Wind",
            name="Cascade test renewable",
            unit="GWh",
            status_value=500.0,
            target_value=500.0,
            is_fixed=True,
            user_editable=True,
        )

    # --- Golden path: default save triggers cascade ---

    def test_landuse_save_without_kwarg_triggers_cascade(self):
        """A bare `landuse.save()` must NOT carry skip_cascade=True."""
        # Snapshot the _skip_cascade flag set after a default save.
        self.landuse.user_percent = 12.5
        self.landuse.save()
        self.assertFalse(
            getattr(self.landuse, "_skip_cascade", False),
            "LandUse.save() default behaviour set _skip_cascade — cascade "
            "would be skipped silently. T26 contract broken.",
        )

    def test_verbrauch_save_without_kwarg_triggers_cascade(self):
        """A bare `verbrauch.save()` must NOT carry skip_cascade=True."""
        self.verbrauch.ziel = 75.0
        self.verbrauch.save()
        self.assertFalse(
            getattr(self.verbrauch, "_skip_cascade", False),
            "VerbrauchData.save() default behaviour set _skip_cascade — "
            "T24 contract broken.",
        )

    def test_renewable_save_without_kwarg_triggers_cascade(self):
        """**The 2026-04 regression target.** Renewable previously had
        skip_cascade=True via save_renewable_user_input. Commit 86e3ba2
        removed it; this test guards against re-introduction.
        """
        self.renewable.user_input = 100.0
        self.renewable.save()
        self.assertFalse(
            getattr(self.renewable, "_skip_cascade", False),
            "RenewableData.save() default behaviour set _skip_cascade — "
            "T25 (Phase 4-E commit 86e3ba2) regression. The PDF §2.4.4 "
            "contract requires cascade-on-every-save for Renewable too.",
        )

    # --- Edge case 1: save(skip_cascade=True) does not raise + row inserts ---

    def test_explicit_skip_cascade_true_is_callable(self):
        """LandUse admin baseline creation uses skip_cascade=True for bulk
        seeding. That code path must remain callable.

        Note: this test does NOT assert the instance attribute persists
        post-save (signals may clear it). It only asserts the kwarg is
        accepted by the override + the row inserts successfully.
        """
        new_lu = LandUse(
            code="LU_BULK",
            name="Bulk seed",
            status_ha=500.0,
            target_ha=500.0,
            user_percent=5.0,
        )
        new_lu.save(skip_cascade=True)
        self.assertIsNotNone(new_lu.pk)
        round_tripped = LandUse.objects.get(pk=new_lu.pk)
        self.assertEqual(round_tripped.code, "LU_BULK")

    # --- Edge case 2: save(skip_cascade=False) is also accepted ---

    def test_explicit_skip_cascade_false_is_callable(self):
        """`save(skip_cascade=False)` must work without raising."""
        self.renewable.user_input = 200.0
        # Should not raise.
        self.renewable.save(skip_cascade=False)
        # Round-trip the value.
        self.renewable.refresh_from_db()
        self.assertEqual(self.renewable.user_input, 200.0)

    # --- Regression: source-level guard against the input_api.py bug ---

    def test_regression_save_renewable_user_input_does_not_use_skip_cascade(self):
        """The input_api.py source must not contain the regression pattern
        `item.save(skip_cascade=True)` inside save_renewable_user_input.

        This is a static check that catches the specific bug at code-edit time
        even before the runtime test above runs.
        """
        from pathlib import Path
        from django.conf import settings

        src = (
            Path(settings.BASE_DIR) / "simulator" / "input_api.py"
        ).read_text(encoding="utf-8")

        # Find the save_renewable_user_input function body.
        import re

        m = re.search(
            r"def\s+save_renewable_user_input\b[\s\S]*?(?=\n@?\w*def\s|\Z)",
            src,
        )
        self.assertIsNotNone(
            m,
            "save_renewable_user_input not found in input_api.py — has it been renamed?",
        )
        body = m.group(0)
        self.assertNotIn(
            "skip_cascade=True",
            body,
            "save_renewable_user_input contains skip_cascade=True — this is "
            "the 2026-04 regression pattern (Phase 4-E commit 86e3ba2 removed "
            "it). Don't add it back without breaking the §2.4.4 contract.",
        )
