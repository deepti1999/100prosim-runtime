from __future__ import annotations

from django.test import SimpleTestCase, TestCase

from simulator.models import LandUse, RenewableData, VerbrauchData
from simulator.ws365_formula_engine import (
    FormulaSpec,
    _build_db_lookup_helpers,
    _compile_expression,
    _evaluate_expression,
    _expression_uses_db_helpers,
    _load_active_formulas,
    _normalize_code,
    _run_daily_stage,
    _run_post_stage,
    _safe_div,
    _to_float_or_zero,
    _preprocess_expression,
    calculate_365_days_with_formulas,
)
from simulator.ws_models import WS365Formula

class WBWS365FormulaEngineUnitTests(SimpleTestCase):
    def test_preprocess_expression_normalizes_shortcuts(self):
        expr = 'IF(a>0; day_prev.ladezust_netto; col_sum.einspeich + col_min.x + col_max.y)'
        processed = _preprocess_expression(expr)
        self.assertEqual(
            processed,
            'IF(a>0, PREV("ladezust_netto"), COL_SUM("einspeich") + COL_MIN("x") + COL_MAX("y"))',
        )

    def test_compile_expression_blank_and_invalid(self):
        self.assertIsNone(_compile_expression("", "blank"))
        with self.assertRaises(ValueError):
            _compile_expression("IF(", "bad")

    def test_expression_helper_detection_is_case_insensitive(self):
        self.assertTrue(_expression_uses_db_helpers('ren_target("9.1.2") + 1'))
        self.assertFalse(_expression_uses_db_helpers("a + b + c"))

    def test_safe_eval_and_numeric_guards(self):
        self.assertEqual(_evaluate_expression(None, {}, "none"), 0.0)
        self.assertEqual(_evaluate_expression(compile("1/0", "<x>", "eval"), {}, "div0"), 0.0)
        self.assertEqual(_evaluate_expression(compile("1e400", "<x>", "eval"), {}, "inf"), 0.0)
        with self.assertRaises(ValueError):
            _evaluate_expression(compile("unknown_name + 1", "<x>", "eval"), {}, "bad_name")

    def test_numeric_helpers(self):
        self.assertEqual(_safe_div(10.0, 0.0), 0.0)
        self.assertEqual(_safe_div(10.0, 2.0), 5.0)
        self.assertEqual(_to_float_or_zero("3.5"), 3.5)
        self.assertEqual(_to_float_or_zero("x"), 0.0)
        self.assertEqual(_normalize_code("9_1_2"), "9.1.2")

    def test_run_daily_stage_uses_day1_expression_and_prev(self):
        ws_data = {
            "solar_promille": [1.0, 1.0, 1.0],
            "wind_promille": [1.0, 1.0, 1.0],
            "heizung_abwaerm_promille": [1.0, 1.0, 1.0],
            "verbrauch_promille": [1.0, 1.0, 1.0],
        }

        daily_formulas = [
            FormulaSpec(
                column_name="a",
                expression="1",
                day1_expression="5",
                expression_code=compile("1", "<a>", "eval"),
                day1_expression_code=compile("5", "<a1>", "eval"),
                stage="daily",
                order=10,
            ),
            FormulaSpec(
                column_name="b",
                expression='PREV("a") + a',
                day1_expression="",
                expression_code=compile('PREV("a") + a', "<b>", "eval"),
                day1_expression_code=None,
                stage="daily",
                order=20,
            ),
        ]

        columns = _run_daily_stage(daily_formulas, ws_data, common_context={}, helper_context={})

        self.assertEqual(columns["a"], [5.0, 1.0, 1.0])
        self.assertEqual(columns["b"], [5.0, 6.0, 2.0])
        self.assertEqual(len(columns["stromverbrauch"]), 3)

    def test_run_post_stage_supports_col_aggregates(self):
        ws_data = {
            "solar_promille": [1.0, 1.0, 1.0],
            "wind_promille": [1.0, 1.0, 1.0],
            "heizung_abwaerm_promille": [1.0, 1.0, 1.0],
            "verbrauch_promille": [1.0, 1.0, 1.0],
        }
        columns = {
            "a": [5.0, 1.0, 1.0],
            "stromverbrauch": [0.0, 0.0, 0.0],
        }
        post_formulas = [
            FormulaSpec(
                column_name="c",
                expression='COL_SUM("a")',
                day1_expression='COL_MIN("a")',
                expression_code=compile('COL_SUM("a")', "<c>", "eval"),
                day1_expression_code=compile('COL_MIN("a")', "<c1>", "eval"),
                stage="post",
                order=10,
            )
        ]
        out = _run_post_stage(post_formulas, columns, ws_data, common_context={}, helper_context={})
        self.assertEqual(out["c"], [1.0, 7.0, 7.0])

class WBWS365FormulaEngineDBTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        RenewableData.objects.create(
            code="9.1.2",
            name="Solar",
            category="renewable",
            unit="GWh",
            status_value=70.0,
            target_value=123.0,
            is_fixed=True,
        )
        VerbrauchData.objects.create(
            code="2.9.2",
            category="Demand",
            unit="GWh",
            status=45.0,
            ziel=456.0,
            is_calculated=False,
        )
        LandUse.objects.create(
            code="LU_2.1",
            name="Solar Area",
            status_ha=11.0,
            target_ha=22.0,
        )

    def test_build_db_lookup_helpers_supports_code_aliases(self):
        helpers = _build_db_lookup_helpers()
        self.assertEqual(helpers["REN_TARGET"]("9_1_2"), 123.0)
        self.assertEqual(helpers["REN_STATUS"]("9.1.2"), 70.0)
        self.assertEqual(helpers["VER_ZIEL"]("2_9_2"), 456.0)
        self.assertEqual(helpers["VER_STATUS"]("2.9.2"), 45.0)
        self.assertEqual(helpers["LU_TARGET"]("2.1"), 22.0)
        self.assertEqual(helpers["LU_STATUS"]("LU_2.1"), 11.0)
        self.assertEqual(helpers["REN_TARGET"]("missing"), 0.0)

    def test_load_active_formulas_splits_daily_and_post_and_detects_helpers(self):
        WS365Formula.objects.create(
            column_name="daily_a",
            stage=WS365Formula.STAGE_DAILY,
            order=10,
            expression='REN_TARGET("9.1.2")',
            day1_expression="",
            is_active=True,
        )
        WS365Formula.objects.create(
            column_name="post_b",
            stage=WS365Formula.STAGE_POST,
            order=20,
            expression='COL_SUM("daily_a")',
            day1_expression='COL_MIN("daily_a")',
            is_active=True,
        )

        daily, post, uses_helpers = _load_active_formulas()
        self.assertTrue(uses_helpers)
        self.assertTrue(any(spec.column_name == "daily_a" for spec in daily))
        self.assertTrue(any(spec.column_name == "post_b" for spec in post))

    def test_calculate_365_days_raises_when_no_active_formulas(self):
        WS365Formula.objects.all().delete()
        ws_data = {
            "solar_promille": [1.0],
            "wind_promille": [1.0],
            "heizung_abwaerm_promille": [1.0],
            "verbrauch_promille": [1.0],
        }
        fixed_values = {
            "ziel_911": 100.0,
            "ziel_913": 10.0,
            "ziel_914": 5.0,
            "ziel_92152": 1.0,
            "verbrauch_7_ziel": 300.0,
            "verbrauch_292_ziel": 10.0,
            "verbrauch_24_ziel": 50.0,
        }
        with self.assertRaises(RuntimeError):
            calculate_365_days_with_formulas(
                solar_value=200.0,
                ws_data=ws_data,
                fixed_values=fixed_values,
                grid_loss_rate=0.1,
                eta_strom_gas=0.65,
                eta_gas_strom=0.585,
            )

    def test_calculate_365_days_applies_shift_fallback_without_post_formulas(self):
        WS365Formula.objects.all().delete()
        WS365Formula.objects.create(
            column_name="ladezust_brutto",
            stage=WS365Formula.STAGE_DAILY,
            order=10,
            expression='PREV("ladezust_brutto") + 1',
            day1_expression="10",
            is_active=True,
        )
        WS365Formula.objects.create(
            column_name="ladezust_netto",
            stage=WS365Formula.STAGE_DAILY,
            order=20,
            expression='PREV("ladezust_netto") - 1',
            day1_expression="2",
            is_active=True,
        )

        ws_data = {
            "solar_promille": [1.0, 1.0, 1.0],
            "wind_promille": [1.0, 1.0, 1.0],
            "heizung_abwaerm_promille": [1.0, 1.0, 1.0],
            "verbrauch_promille": [1.0, 1.0, 1.0],
        }
        fixed_values = {
            "ziel_911": 100.0,
            "ziel_913": 10.0,
            "ziel_914": 5.0,
            "ziel_92152": 1.0,
            "verbrauch_7_ziel": 300.0,
            "verbrauch_292_ziel": 10.0,
            "verbrauch_24_ziel": 50.0,
        }

        result = calculate_365_days_with_formulas(
            solar_value=200.0,
            ws_data=ws_data,
            fixed_values=fixed_values,
            grid_loss_rate=0.1,
            eta_strom_gas=0.65,
            eta_gas_strom=0.585,
        )

        self.assertEqual(result["daily_data"][0]["ladezust_abs_vorl_tl"], 0.0)
        self.assertEqual(result["daily_data"][1]["ladezust_abs_vorl_tl"], 1.0)
        self.assertEqual(result["daily_data"][2]["ladezust_abs_vorl_tl"], 2.0)

        self.assertEqual(result["daily_data"][0]["ladezust_absolute"], 2.0)
        self.assertEqual(result["daily_data"][1]["ladezust_absolute"], 1.0)
        self.assertEqual(result["daily_data"][2]["ladezust_absolute"], 0.0)
