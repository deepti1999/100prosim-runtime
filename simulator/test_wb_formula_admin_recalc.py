from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase


class FormulaAdminRecalcSignalTests(TestCase):
    def setUp(self):
        from simulator.models import LandUse, Region

        self.region, _ = Region.objects.get_or_create(
            code="DE",
            defaults={"display_name": "Deutschland"},
        )
        self.user = get_user_model().objects.create_user(
            username="formula_scope_user",
            password="x",
        )
        LandUse.all_objects.create(
            owner=None,
            region=self.region,
            code="LU_FORMULA_SCOPE",
            name="Formula scope template",
        )
        LandUse.all_objects.create(
            owner=self.user,
            region=self.region,
            code="LU_FORMULA_SCOPE",
            name="Formula scope user",
        )

    def test_formula_recalc_scopes_include_template_and_user_workspace(self):
        from simulator.signals import _formula_recalc_scopes

        scopes = set(_formula_recalc_scopes())

        self.assertIn((None, "DE"), scopes)
        self.assertIn((self.user.id, "DE"), scopes)

    def test_formula_save_schedules_dependent_recalc(self):
        from simulator.models import Formula

        with patch("simulator.signals._schedule_formula_dependent_recalc") as schedule:
            Formula.objects.create(
                key="TEST_FORMULA_ADMIN_RECALC",
                category="renewable",
                expression="1 + 1",
                is_active=True,
            )

        schedule.assert_called_with("renewable", "TEST_FORMULA_ADMIN_RECALC")

    def test_formula_recalc_is_queued_for_worker(self):
        from simulator.models import BalanceJob
        from simulator.signals import _queue_formula_dependent_recalc

        with patch("simulator.signals._invalidate_formula_runtime_caches"):
            _queue_formula_dependent_recalc("renewable", "TEST_QUEUED_FORMULA")

        jobs = BalanceJob.objects.filter(
            job_type=BalanceJob.TYPE_LANDUSE_RECALC,
            payload__trigger="formula_admin",
            payload__formula_key="TEST_QUEUED_FORMULA",
        ).order_by("created_by_id")

        self.assertEqual(jobs.count(), 2)
        self.assertEqual(
            {(job.created_by_id, job.payload["region_code"]) for job in jobs},
            {(None, "DE"), (self.user.id, "DE")},
        )

    def test_formula_variable_save_schedules_dependent_recalc(self):
        from simulator.models import Formula, FormulaVariable

        with patch("simulator.signals._schedule_formula_dependent_recalc"):
            formula = Formula.objects.create(
                key="TEST_FORMULA_VARIABLE_RECALC",
                category="renewable",
                expression="x + 1",
                is_active=True,
            )

        with patch("simulator.signals._schedule_formula_dependent_recalc") as schedule:
            FormulaVariable.objects.create(
                formula=formula,
                variable_name="x",
                source_type=FormulaVariable.LITERAL,
                source_key="1",
            )

        schedule.assert_called_with("renewable", "TEST_FORMULA_VARIABLE_RECALC")
