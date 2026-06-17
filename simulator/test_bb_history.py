"""History logging and the current prepared Historie page."""
import json
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from simulator.models import (
    BaselineSnapshot,
    LandUse,
    ModificationHistoryEntry,
    RenewableData,
    ScenarioSnapshot,
    VerbrauchData,
)
from simulator.page_historie import _history_values_for_source


class ModificationHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="history_user", password="x", is_staff=False
        )

        cls.root = LandUse(
            code="LU_0",
            name="Bodenfläche gesamt",
            status_ha=35759529.0,
            target_ha=35759529.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=None,
        )
        cls.root.save(skip_cascade=True)
        cls.child = LandUse(
            code="LU_2.1",
            name="Solare Freiflächen",
            status_ha=19628.0,
            target_ha=676910.0,
            user_percent=7.0,
            increase_limit_baseline_percent=10.0,
            parent=cls.root,
        )
        cls.child.save(skip_cascade=True)
        cls.landuse_lu1 = LandUse(
            code="LU_1",
            name="Siedlung (Gebäude- & Freifläche)",
            status_ha=3380079.0,
            target_ha=3645799.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=cls.root,
        )
        cls.landuse_lu1.save(skip_cascade=True)
        cls.landuse_lu11 = LandUse(
            code="LU_1.1",
            name="Solare Dachflächen",
            status_ha=34243.0,
            target_ha=199398.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=cls.landuse_lu1,
        )
        cls.landuse_lu11.save(skip_cascade=True)
        cls.landuse_lu2 = LandUse(
            code="LU_2",
            name="Landwirtschaftsfläche (LF)",
            status_ha=18020717.0,
            target_ha=17754997.0,
            user_percent=100.0,
            increase_limit_baseline_percent=100.0,
            parent=cls.root,
        )
        cls.landuse_lu2.save(skip_cascade=True)
        for code, name, status_ha, target_ha in [
            ("LU_6", "Windparkflächen onshore", 172556.0, 715289.0),
            ("LU_2.2.2", "Energiepfl. (Biogas)", 1410000.0, 1307000.0),
            ("LU_2.2.3", "Energiepfl. (Pflanzenöl)", 665000.0, 303000.0),
            ("LU_2.2.4", "Energiepfl. (Ethanol)", 216200.0, 0.0),
            ("LU_2.2.5", "Energiepfl. (Kurzumtr.)", 11200.0, 11200.0),
        ]:
            row = LandUse(
                code=code,
                name=name,
                status_ha=status_ha,
                target_ha=target_ha,
                user_percent=100.0,
                increase_limit_baseline_percent=100.0,
                parent=cls.landuse_lu2,
            )
            row.save(skip_cascade=True)

        cls.verbrauch = VerbrauchData.objects.create(
            code="1.1.2",
            category="Test",
            unit="GWh",
            status=100.0,
            ziel=80.0,
            is_calculated=False,
        )
        for code, status, ziel, category, unit in [
            ("2.1.1", 44.7, 44.7, "Wohnfläche pro Person", "m² / Kopf"),
            ("2.2.1", 100.0, 100.0, "Gewerbefläche pro Person", "% v. Status"),
            ("2.4.1", 136.0, 75.0, "Spez.Raumwärmebed.Status/Saniert", "kWh / (m² * a)"),
            ("2.4.5", 0.0, 33.0, "Gebäudeanteil mit Ziel-Wärmeschutz", "% v. Bestand"),
            ("2.10", 798867.0, 663539.0, "Endenergieverbrauch GW gesamt", "GWh/a"),
            ("4.1.1.1", 100.0, 100.0, "Zieleinfluss Pers.-Verkehrsleist./Pers.", "% v. Status"),
            ("4.1.2", 32.6, 32.6, "davon Güterverkehr u. a. (GVk)", "% v. Status"),
            ("5.1", 100.0, 100.0, "Zieleinfluss Luftverk.-Leistung/Person", "% v. Status"),
            ("4.1.1.5", 8.6, 86.0, "Anteil Elektrotraktion an PvK-Leistung", "% PVk-Leist"),
            ("4.1.1.15.1", None, None, "Brennstoffzellen Personenverkehr", ""),
            ("4.1.2.5", 18.6, 84.0, "Anteil Elektrotraktion an GVk-Leistung", "% GVk-Leist."),
            ("4.1.2.15.1", None, None, "Brennstoffzellen Güterverkehr", ""),
            ("3.2.1", 100.0, 100.0, "Prozesswärme Bedarfsniveau", "% v. Status"),
            ("1.3.2", 100.0, 100.0, "Industriestrom Bedarfsniveau", "% v. Status"),
            ("3.4", 27.0, 60.0, "Brennstoffanteil an Prozesswärme", "% v. Status"),
            ("9.1.1", 53.0, 100.0, "Kunststofferzeugung / Kopf", "% v. Status"),
            ("1.2.2", 100.0, 100.0, "Zieleinfluss Handels-/Dienstl.-Vol./Pers.", "%"),
            ("1.2.4", 95.0, 100.0, "Zieleinfluss Prozess-Effizienz", "%"),
            ("1.3.4", 95.0, 100.0, "Zieleinfluss Prozess-Effizienz", "%"),
            ("1.4", 329214.0, 312753.0, "Endverbrauch Strom für KLIK gesamt", "GWh/a"),
            ("3.7", 555395.0, 490251.0, "Endenergieverbrauch PW gesamt", "GWh/a"),
            ("9.1.2", 197841.0, 197841.0, "Grundstoff gesamt Status", "GWh/a"),
            ("9.1.4", 0.0, 76545.0, "Synthetisches Methan als Grundstoff", "GWh/a"),
            ("6.0", 753713.0, 388749.0, "Endenergieverbrauch Mobile Anwendungen", "GWh/a"),
        ]:
            VerbrauchData.objects.create(
                code=code,
                category=category,
                unit=unit,
                status=status,
                ziel=ziel,
                is_calculated=False,
            )
        for code, status, target, name, unit in [
            ("9.4.2", 0.0, 0.0, "Stromeinfuhr (Erneuerb.) aus dem Ausland", "GWh/a"),
            ("9.2", 256797.0, 1931900.0, "Bruttostromerzeugung Erneuerbar", "GWh/a"),
            ("9.2.1.5.2.2", 0.0, 0.0, "davon extern für Importwasserstoff", "GWh/a"),
            ("9.2.1.5.2", 0.0, 385934.0, "Stromeinsatz Wasserstofferzeugung", "GWh/a"),
            ("7.1.2.2", 23273.0, 526888.0, "Luftgekoppelte WP", "GWh/a"),
            ("7.1.4.2", 11052.0, 51801.0, "Erdreichgekoppelte WP", "GWh/a"),
            ("4.1.3.1", 73.3, 0.0, "davon für Gebäudewärme", "% v. Gesamt"),
            ("4.1.3", 120449.0, 71302.0, "Energieholzaufkommen gesamt", "GWh/a"),
            ("1.1.1.1.2", 8449.0, 11515.0, "Gebäudewärme", "GWh"),
            ("9.2.1.1", 0.0, 0.0, "Wasserstoff elektrischer Anteil", "GWh/a"),
            ("9.2.1.4.2", 95681.0, 0.0, "Wasserstoff Kraftstoffsynthese", "GWh/a"),
            ("1.1.1.1", 6.4, 1.1, "Anteil an solaren Dachflächen", "%"),
            ("1.1.2.1.2.2", 47857.0, 394410.0, "Installierte Leistung", "MW"),
            ("1.2.1.2.2", 19530.0, 902546.0, "Installierte Leistung", "MW"),
            ("2.1.1.2", 59502.0, 188234.0, "Installierte Leistung", "MW"),
            ("2.2.1", 8337.0, 70000.0, "Install. Offshore-Leistung Deutschland", "MW"),
            ("4.1.1.1.1", 53.6, 33.2, "Energet.genutzter Anteil am Zuwachs", "%"),
            ("4.2.1.1", 0.2, 33.0, "Energet.genutzter Teil am Strohanfall", "%"),
            ("5.1.1", 50.9, 40.8, "Biogas - Methanertrag", "MWh/ha/a"),
            ("9.3.3", 0.0, 241727.0, "Erforderliche Speicherkapazität", "GWh"),
            ("2.1.1.2.2", 111532.0, 479997.0, "Bruttostromerzeugung onshore", "GWh/a"),
            ("2.2.1.2.3", 23535.0, 226240.0, "Bruttostromerzeugung Deutschland offshore", "GWh/a"),
            ("9.1.2", 1201630.0, 0.0, "Solarstrom", "GWh/a"),
            ("9.1.3", 19509.0, 19509.0, "Wasserkraft", "GWh/a"),
            ("10.9.1.1", 110597.0, 0.0, "Biobrennstoffe gasförmig", "GWh/a"),
            ("10.9.1.2", 4303.0, 0.0, "Biobrennstoffe flüssig", "GWh/a"),
            ("10.9.1.3", 130029.0, 0.0, "Biobrennstoffe fest", "GWh/a"),
            ("7.1.2.3", 401438.0, 0.0, "Umgebungswärme Luft", "GWh/a"),
            ("7.1.4.3", 41229.0, 0.0, "Umgebungswärme Erdreich", "GWh/a"),
        ]:
            RenewableData.objects.create(
                code=code,
                category="Test",
                name=name,
                unit=unit,
                status_value=status,
                target_value=target,
            )

    def setUp(self):
        self.client.force_login(self.user)

    def test_landuse_edit_writes_history_row(self):
        self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": "LU_2.1", "user_percent": 3.5}),
            content_type="application/json",
        )
        entries = ModificationHistoryEntry.objects.filter(code="LU_2.1")
        self.assertEqual(entries.count(), 1)
        entry = entries.first()
        self.assertEqual(entry.model_label, "LandUse")
        self.assertEqual(entry.field, "user_percent")
        self.assertEqual(entry.source, "user")
        self.assertAlmostEqual(float(entry.value_before), 7.0)
        self.assertAlmostEqual(float(entry.value_after), 3.5)
        self.assertEqual(entry.owner, self.user)

    def test_verbrauch_edit_writes_history_row(self):
        self.client.post(
            reverse("simulator:save_verbrauch_user_input"),
            data=json.dumps({"code": "1.1.2", "user_percent": 95}),
            content_type="application/json",
        )
        entries = ModificationHistoryEntry.objects.filter(code="1.1.2")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().model_label, "VerbrauchData")

    def test_history_page_shows_prepared_table_not_log_entries(self):
        other = get_user_model().objects.create_user(username="other", password="x")
        ModificationHistoryEntry.objects.create(
            owner=self.user, model_label="LandUse", code="LU_2.1",
            field="user_percent", value_before=7.0, value_after=3.5,
        )
        ModificationHistoryEntry.objects.create(
            owner=other, model_label="LandUse", code="LU_1",
            field="user_percent", value_before=1.0, value_after=2.0,
        )

        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Randbedingungen")
        self.assertContains(response, "Bevölkerungsentwicklung")
        self.assertContains(response, "84.669.326")
        self.assertContains(response, "Gebäude")
        self.assertContains(response, "Wohnfläche / Kopf")
        self.assertContains(response, "Verkehr")
        self.assertContains(response, "Produktion (Güter)")
        self.assertContains(response, "Erzeugung (Energie)")
        self.assertContains(response, "Klassische Stromanwendungen (KLIK)")
        self.assertContains(response, "Endenergie nach Anwendungsbereichen")
        self.assertContains(response, "Primärenergie-Beiträge nach Quellen")
        self.assertContains(response, "Add on")
        self.assertContains(response, "Personenverkehrsleistung /Kopf")
        self.assertContains(response, "Stromspeicherkapaz. (Wasserst.)")
        self.assertContains(response, "Stromanwend.-Effizienz Haushalte")
        self.assertContains(response, "Fossile/atomare Brennstoffe")
        self.assertContains(response, "Rückverstromungs-Leistung (elektr.)")
        self.assertContains(response, "1.931.900")
        self.assertContains(response, "385.934")
        self.assertContains(response, "44,7")
        self.assertContains(response, "3.645.799")
        self.assertContains(response, "32,6")
        self.assertContains(response, "8,6")
        self.assertContains(response, "86")
        self.assertContains(response, "18,6")
        self.assertContains(response, "84")
        self.assertContains(response, "(Passiv)")
        self.assertContains(response, "Prozesswärme Bedarfsniveau")
        self.assertContains(response, "Brennstoffanteil an Prozesswärme")
        self.assertContains(response, "Kunststofferzeugung / Kopf")
        self.assertContains(response, "95.681")
        self.assertContains(response, "34.243")
        self.assertContains(response, "199.398")
        self.assertContains(response, "394.410")
        self.assertContains(response, "17.754.997")
        self.assertContains(response, "902.546")
        self.assertContains(response, "715.289")
        self.assertContains(response, "70.000")
        self.assertContains(response, "33,2")
        self.assertContains(response, "1.307.000")
        self.assertContains(response, "303.000")
        self.assertContains(response, "241.727")
        self.assertContains(response, "312.753")
        self.assertContains(response, "490.251")
        self.assertContains(response, "197.841")
        self.assertContains(response, "76.545")
        self.assertContains(response, "388.749")
        self.assertContains(response, "479.997")
        self.assertContains(response, "226.240")
        self.assertContains(response, "1.201.630")
        self.assertContains(response, "110.597")
        self.assertContains(response, "130.029")
        self.assertContains(response, "401.438")
        self.assertContains(response, "41.229")
        self.assertNotContains(response, "Modifikations-Historie")
        self.assertNotContains(response, "LU_2.1")
        self.assertNotContains(response, "value_before")

    def test_history_page_renders_same_structure_for_empty_user(self):
        fresh = get_user_model().objects.create_user(username="fresh", password="x")
        self.client.force_login(fresh)
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historie")
        self.assertContains(response, "Status")
        self.assertContains(response, "Ziel")
        self.assertNotContains(response, "Referenz-/Herkunftsspalten")
        self.assertNotContains(response, "Noch keine Modifikationen")

    def test_history_table_keeps_unmapped_status_and_target_cells_empty(self):
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        main = body.split("<main")[1].split("</main>")[0] if "<main" in body else body
        self.assertIn("history-value", main)
        self.assertIn("84.669.326", main)
        self.assertIn("1.931.900", main)
        self.assertNotIn("2.443.849", main)

    def test_history_table_uses_clean_display_numbers(self):
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        numbers = re.findall(r'class="history-row-number">(\d+)</td>', body)
        self.assertGreater(len(numbers), 5)
        self.assertEqual(numbers[:5], ["1", "2", "3", "4", "5"])

    def test_history_building_renovation_standard_is_derived_from_kwh_row(self):
        payload = {
            "verbrauch": [
                {
                    "code": "2.4.1",
                    "status": 136.0,
                    "ziel": 75.0,
                }
            ]
        }

        status, target = _history_values_for_source(
            ("verbrauch_status_percent", "2.4.1"),
            "% v. Status",
            payload,
        )

        self.assertEqual(status, "100")
        self.assertEqual(target, "55,1")

    def test_history_building_renovated_share_uses_verbrauch_245(self):
        status, target = _history_values_for_source(
            ("verbrauch", "2.4.5"),
            "% v. Bestand",
            payload=None,
            fallback_to_live=True,
        )

        self.assertEqual(status, "0")
        self.assertEqual(target, "33")

    def test_history_heat_pump_share_uses_wp_rows_over_building_heat_total(self):
        status, target = _history_values_for_source(
            ("heat_pump_building_heat_share", ""),
            "%",
            payload=None,
            fallback_to_live=True,
        )

        self.assertEqual(status, "4,3")
        self.assertEqual(target, "87,2")

    def test_history_solar_thermal_share_uses_solar_thermal_over_building_heat_total(self):
        status, target = _history_values_for_source(
            ("solar_thermal_building_heat_share", ""),
            "% v. Gesamt",
            payload=None,
            fallback_to_live=True,
        )

        self.assertEqual(status, "1,1")
        self.assertEqual(target, "1,7")

    def test_history_compares_baseline_against_saved_scenario(self):
        BaselineSnapshot.objects.create(
            key="global",
            payload={
                "renewable": [
                    {
                        "code": "9.2",
                        "status_value": 1000.0,
                        "target_value": 2000.0,
                    }
                ]
            },
        )
        scenario = ScenarioSnapshot.objects.create(
            owner=self.user,
            name="Szenario Vergleich",
            payload={
                "renewable": [
                    {
                        "code": "9.2",
                        "status_value": 3000.0,
                        "target_value": 4000.0,
                    }
                ]
            },
        )
        session = self.client.session
        session["active_scenario_scope"] = f"user:{self.user.id}"
        session["active_scenario_id"] = scenario.id
        session.save()

        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Baseline Status")
        self.assertContains(response, "Baseline Ziel")
        self.assertContains(response, "Szenario Vergleich Status")
        self.assertContains(response, "Szenario Vergleich Ziel")
        self.assertContains(response, "1.000")
        self.assertContains(response, "2.000")
        self.assertContains(response, "3.000")
        self.assertContains(response, "4.000")

    def test_history_shows_all_saved_scenarios_side_by_side(self):
        ScenarioSnapshot.objects.create(
            owner=self.user,
            name="Szenario Eins",
            payload={
                "renewable": [
                    {"code": "9.2", "status_value": 111.0, "target_value": 222.0}
                ]
            },
        )
        ScenarioSnapshot.objects.create(
            owner=self.user,
            name="Szenario Zwei",
            payload={
                "renewable": [
                    {"code": "9.2", "status_value": 333.0, "target_value": 444.0}
                ]
            },
        )

        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Szenario Eins Status")
        self.assertContains(response, "Szenario Eins Ziel")
        self.assertContains(response, "Szenario Zwei Status")
        self.assertContains(response, "Szenario Zwei Ziel")
        self.assertContains(response, "111")
        self.assertContains(response, "222")
        self.assertContains(response, "333")
        self.assertContains(response, "444")

    def test_history_staff_user_sees_own_workspace_scenarios_not_global_scenarios(self):
        staff_user = get_user_model().objects.create_user(
            username="history_staff",
            password="x",
            is_staff=True,
        )
        ScenarioSnapshot.objects.create(
            owner=None,
            name="Ideal scenario",
            payload={
                "renewable": [
                    {"code": "9.2", "status_value": 111.0, "target_value": 222.0}
                ]
            },
        )
        ScenarioSnapshot.objects.create(
            owner=staff_user,
            name="verbrauch",
            payload={
                "renewable": [
                    {"code": "9.2", "status_value": 333.0, "target_value": 444.0}
                ]
            },
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("simulator:historie"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "verbrauch Status")
        self.assertContains(response, "verbrauch Ziel")
        self.assertContains(response, "333")
        self.assertContains(response, "444")
        self.assertNotContains(response, "Ideal scenario Status")
        self.assertNotContains(response, "Ideal scenario Ziel")

    def test_history_page_has_changed_value_highlight_control(self):
        response = self.client.get(reverse("simulator:historie"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="historyHighlightMode"')
        self.assertContains(response, "Keine Hervorhebung")
        self.assertContains(response, "Nur geänderte Werte anzeigen")
        self.assertContains(response, 'data-history-value-group="status"')
        self.assertContains(response, 'data-history-value-group="target"')
        self.assertContains(response, "is-history-changed")
        self.assertContains(response, "is-history-unchanged")
