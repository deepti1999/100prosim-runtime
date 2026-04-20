from django.test import TestCase

from simulator.models import RenewableData, VerbrauchData, WS365Formula
from simulator.ws_api import _build_ws_columns
from simulator.ws_365_service import get_fixed_values, get_ws_base_data
from simulator.ws365_core import _calculate_365_days_legacy, calculate_365_days
from simulator.ws_models import WSData

class WS365FormulaEngineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        VerbrauchData.objects.bulk_create(
            [
                VerbrauchData(
                    code="7",
                    category="Total demand",
                    unit="GWh",
                    status=0.0,
                    ziel=1000.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="2.9.2",
                    category="Raumwaerme",
                    unit="GWh",
                    status=0.0,
                    ziel=120.0,
                    is_calculated=False,
                ),
                VerbrauchData(
                    code="2.4",
                    category="Raumwaerme percent",
                    unit="%",
                    status=0.0,
                    ziel=35.0,
                    is_calculated=False,
                ),
            ]
        )

        RenewableData.objects.bulk_create(
            [
                RenewableData(
                    code="9.1.1",
                    name="Wind",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=420.0,
                    is_fixed=True,
                ),
                RenewableData(
                    code="9.1.2",
                    name="Solar",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=380.0,
                    is_fixed=True,
                ),
                RenewableData(
                    code="9.1.3",
                    name="Other",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=200.0,
                    is_fixed=True,
                ),
                RenewableData(
                    code="9.1.4",
                    name="Bio",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=90.0,
                    is_fixed=True,
                ),
                RenewableData(
                    code="9.2.1.5.2",
                    name="Subtraction",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=60.0,
                    is_fixed=True,
                ),
                RenewableData(
                    code="9.1.5",
                    name="New renewable source",
                    category="renewable",
                    unit="GWh",
                    status_value=0.0,
                    target_value=50.0,
                    is_fixed=True,
                ),
            ]
        )

        ws_rows = []
        for day in range(1, 366):
            ws_rows.append(
                WSData(
                    tag_im_jahr=day,
                    solar_promille=2.0 + (day % 9),
                    wind_promille=3.0 + (day % 7),
                    heizung_abwaerm_promille=1.0 + (day % 5),
                    verbrauch_promille=2.0 + (day % 11),
                )
            )
        WSData.objects.bulk_create(ws_rows, batch_size=500)

    def _run(self):
        ws_data = get_ws_base_data()
        fixed_values = get_fixed_values()
        solar_value = fixed_values["ziel_912"]
        return ws_data, fixed_values, solar_value

    def test_db_formula_engine_matches_legacy_defaults(self):
        ws_data, fixed_values, solar_value = self._run()

        legacy = _calculate_365_days_legacy(solar_value, ws_data, fixed_values)
        current = calculate_365_days(solar_value, ws_data, fixed_values)

        self.assertEqual(len(current["daily_data"]), 365)
        self.assertAlmostEqual(current["annual_electricity"], legacy["annual_electricity"], places=6)
        self.assertAlmostEqual(current["storage_drift"], legacy["storage_drift"], places=6)
        self.assertAlmostEqual(current["einspeich_sum"], legacy["einspeich_sum"], places=6)
        self.assertAlmostEqual(current["abregelung_sum"], legacy["abregelung_sum"], places=6)

    def test_changing_formula_in_db_changes_ws_output(self):
        ws_data, fixed_values, solar_value = self._run()
        before = calculate_365_days(solar_value, ws_data, fixed_values)

        WS365Formula.objects.filter(column_name="selbstentl").update(expression="1")

        after = calculate_365_days(solar_value, ws_data, fixed_values)

        self.assertEqual(after["daily_data"][0]["selbstentl"], 1.0)
        self.assertNotEqual(
            after["daily_data"][0]["ladezust_netto"],
            before["daily_data"][0]["ladezust_netto"],
        )

    def test_formula_can_reference_new_renewable_code_directly(self):
        ws_data, fixed_values, solar_value = self._run()
        before = calculate_365_days(solar_value, ws_data, fixed_values)

        WS365Formula.objects.filter(column_name="solar_strom").update(
            expression='(ziel_912 + REN_TARGET("9.1.5")) * pct * solar_promille / 1000'
        )
        after = calculate_365_days(solar_value, ws_data, fixed_values)

        self.assertGreater(after["daily_data"][0]["solar_strom"], before["daily_data"][0]["solar_strom"])

    def test_dynamic_column_config_includes_new_formula_column(self):
        WS365Formula.objects.create(
            column_name="new_data",
            stage=WS365Formula.STAGE_DAILY,
            order=999,
            expression='REN_TARGET("9.1.5") * pct * solar_promille / 1000',
            is_active=True,
        )

        columns = _build_ws_columns([{"day": 1, "new_data": 1.0}])
        keys = [col["key"] for col in columns]
        labels = [col["label"] for col in columns]

        self.assertIn("new_data", keys)
        self.assertIn("New Data", labels)

    def test_calculate_365_days_outputs_new_formula_column(self):
        ws_data, fixed_values, solar_value = self._run()

        WS365Formula.objects.create(
            column_name="new_data",
            stage=WS365Formula.STAGE_DAILY,
            order=999,
            expression='REN_TARGET("9.1.5") * pct * solar_promille / 1000',
            is_active=True,
        )

        result = calculate_365_days(solar_value, ws_data, fixed_values)
        self.assertIn("new_data", result["daily_data"][0])
