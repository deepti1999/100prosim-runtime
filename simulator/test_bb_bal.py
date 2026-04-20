import sqlite3
from pathlib import Path
from unittest import SkipTest
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from simulator.models import BalanceJob, VerbrauchData

class BlackBoxBalanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._seed_core_realdata()
        cls.user = get_user_model().objects.create_user(
            username="bb_bal_admin",
            password="test-pass-123",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    @classmethod
    def _seed_core_realdata(cls):
        """
        Seed the test DB from project baseline SQLite so WS balance endpoints
        execute real formulas/rows (non-mocked integration behavior).
        """
        if connection.vendor != "sqlite":
            raise SkipTest("Real-data WS balance tests require sqlite backend.")

        base_dir = Path(settings.BASE_DIR)
        source_candidates = [
            base_dir / "db_baseline.sqlite3",
            base_dir / "db.sqlite3",
        ]
        source_path = next((p for p in source_candidates if p.exists()), None)
        if source_path is None:
            raise SkipTest("No baseline sqlite file found for real-data WS tests.")

        tables = {
            "simulator_formula": None,
            "simulator_formulavariable": None,
            "simulator_landuse": "owner_id IS NULL",
            "simulator_renewabledata": "owner_id IS NULL",
            "simulator_verbrauchdata": "owner_id IS NULL",
            "simulator_wsdata": "owner_id IS NULL",
        }

        delete_order = [
            "simulator_wsdata",
            "simulator_renewabledata",
            "simulator_verbrauchdata",
            "simulator_landuse",
            "simulator_formulavariable",
            "simulator_formula",
        ]
        insert_order = [
            "simulator_formula",
            "simulator_formulavariable",
            "simulator_landuse",
            "simulator_renewabledata",
            "simulator_verbrauchdata",
            "simulator_wsdata",
        ]

        with sqlite3.connect(str(source_path)) as src_conn:
            src_conn.row_factory = sqlite3.Row
            with connection.cursor() as dst_cur:
                dst_cur.execute("PRAGMA foreign_keys=OFF")
                for table in delete_order:
                    dst_cur.execute(f'DELETE FROM "{table}"')

                for table in insert_order:
                    cls._copy_table(src_conn, dst_cur, table, where_clause=tables[table])

                dst_cur.execute("PRAGMA foreign_keys=ON")

    @staticmethod
    def _copy_table(src_conn, dst_cur, table_name, where_clause=None):
        src_cols = [
            row[1]
            for row in src_conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        ]
        dst_cur.execute(f'PRAGMA table_info("{table_name}")')
        dst_cols = [row[1] for row in dst_cur.fetchall()]
        common_cols = [col for col in src_cols if col in dst_cols]
        extra_insert_defaults = {}
        if table_name == "simulator_renewabledata" and "user_editable" in dst_cols and "user_editable" not in common_cols:
            extra_insert_defaults["user_editable"] = 0

        if not common_cols and not extra_insert_defaults:
            return

        select_cols = list(common_cols)
        insert_cols = list(common_cols) + list(extra_insert_defaults.keys())

        quoted_select_cols = ", ".join(f'"{col}"' for col in select_cols)
        quoted_insert_cols = ", ".join(f'"{col}"' for col in insert_cols)
        select_sql = f'SELECT {quoted_select_cols} FROM "{table_name}"'
        use_where = where_clause and ("owner_id" in src_cols)
        if use_where:
            select_sql = f"{select_sql} WHERE {where_clause}"

        rows = src_conn.execute(select_sql).fetchall()
        if not rows:
            return

        placeholders = ", ".join(["?"] * len(insert_cols))
        insert_sql = f'INSERT INTO "{table_name}" ({quoted_insert_cols}) VALUES ({placeholders})'
        normalized_rows = []
        for row in rows:
            values = []
            for col in select_cols:
                value = row[col]
                if col == "user_editable" and value is None:
                    value = 0
                values.append(value)
            for col in extra_insert_defaults:
                values.append(extra_insert_defaults[col])
            normalized_rows.append(tuple(values))
        dst_cur.executemany(insert_sql, normalized_rows)

    @override_settings(DEBUG=True)
    def test_first_ws_button_passes_when_electricity_and_drift_criteria_hold(self):
        response = self.client.post(reverse("simulator:ws_api_apply_balance"))
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertIn("storage_drift", payload)
        self.assertIn("annual_electricity", payload)

        drift_ok = abs(float(payload.get("storage_drift") or 0.0)) <= 0.1
        electricity_present = float(payload.get("annual_electricity") or 0.0) > 0.0
        self.assertTrue(
            drift_ok and electricity_present,
            f"Expected drift<=0.1 and annual_electricity>0, got drift={payload.get('storage_drift')}, annual_electricity={payload.get('annual_electricity')}",
        )

    def test_ws_balance_job_status_reports_running_and_succeeded_states(self):
        job = BalanceJob.objects.create(
            job_type=BalanceJob.TYPE_SOLAR_WS_ONLY,
            status=BalanceJob.STATUS_QUEUED,
            created_by=self.user,
            payload={},
        )

        queued_response = self.client.get(
            reverse("simulator:ws_api_balance_job_status", kwargs={"job_id": job.id})
        )
        queued_payload = queued_response.json()

        self.assertEqual(queued_response.status_code, 200)
        self.assertTrue(queued_payload["success"])
        self.assertEqual(queued_payload["status"], BalanceJob.STATUS_QUEUED)
        self.assertIn("message", queued_payload)

        job.status = BalanceJob.STATUS_SUCCEEDED
        job.result = {"summary": {"status": "balanced"}}
        job.save(update_fields=["status", "result", "updated_at"])

        done_response = self.client.get(
            reverse("simulator:ws_api_balance_job_status", kwargs={"job_id": job.id})
        )
        done_payload = done_response.json()

        self.assertEqual(done_response.status_code, 200)
        self.assertTrue(done_payload["success"])
        self.assertEqual(done_payload["status"], BalanceJob.STATUS_SUCCEEDED)
        self.assertIn("result", done_payload)

    @override_settings(DEBUG=True)
    def test_second_ws_button_passes_when_sector_gaps_and_drift_are_within_limits(self):
        response = self.client.post(reverse("simulator:ws_api_apply_full_balance"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertIn("heat_balance", payload)
        self.assertIn("after", payload["heat_balance"])

        after = payload["heat_balance"]["after"]
        sectors_ok = (
            abs(float(after["gebaeudewaerme"]["gap"])) <= 100.0
            and abs(float(after["prozesswaerme"]["gap"])) <= 100.0
            and abs(float(after["mobile_anwendungen"]["gap"])) <= 100.0
        )
        drift_ok = abs(float(payload.get("storage_drift") or 0.0)) <= 0.1
        self.assertTrue(
            sectors_ok and drift_ok,
            f"Expected sectors<=100 and drift<=0.1, got after={after}, drift={payload.get('storage_drift')}",
        )

    @override_settings(DEBUG=False)
    def test_ws_apply_balance_wind_queues_wind_ws_job(self):
        response = self.client.post(reverse("simulator:ws_api_apply_balance_wind"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertTrue(payload["queued"])

        job = BalanceJob.objects.get(id=payload["job_id"])
        self.assertEqual(job.job_type, BalanceJob.TYPE_WIND_WS_ONLY)
        self.assertEqual(job.created_by_id, self.user.id)

    @override_settings(DEBUG=True)
    def test_e2e_verbrauch_change_recalc_then_ws_button1_button2_balances(self):
        """
        End-to-end black-box flow:
        1) Change demand input in Verbrauch (2.4.1: 75% -> 80%)
        2) Recalculate Verbrauch twice
        3) Recalculate renewable page once
        4) WS button 1 (storage balance)
        5) WS button 2 (sector + WS balance)
        6) Assert final drift and sector gaps are within tolerances.
        """
        item = VerbrauchData.objects.filter(code="2.4.1").first()
        if item is None:
            self.skipTest("Requires VerbrauchData code 2.4.1 in baseline seed.")

        update_response = self.client.post(
            reverse("simulator:save_verbrauch_user_input"),
            data=json.dumps({"code": "2.4.1", "user_percent": 80.0}),
            content_type="application/json",
        )
        update_payload = update_response.json()
        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(update_payload["success"])

        updated = VerbrauchData.objects.get(code="2.4.1")
        self.assertAlmostEqual(float(updated.user_percent or 0.0), 80.0, places=6)

        recalc_v1 = self.client.post(reverse("simulator:recalc_verbrauch"))
        recalc_v1_payload = recalc_v1.json()
        self.assertEqual(recalc_v1.status_code, 200)
        self.assertEqual(recalc_v1_payload["status"], "ok")

        recalc_v2 = self.client.post(reverse("simulator:recalc_verbrauch"))
        recalc_v2_payload = recalc_v2.json()
        self.assertEqual(recalc_v2.status_code, 200)
        self.assertEqual(recalc_v2_payload["status"], "ok")

        recalc_ren = self.client.post(reverse("simulator:recalc_renewables"))
        recalc_ren_payload = recalc_ren.json()
        self.assertEqual(recalc_ren.status_code, 200)
        self.assertTrue(recalc_ren_payload["success"])

        full_sync = self.client.post(reverse("simulator:run_full_recalc"))
        full_sync_payload = full_sync.json()
        self.assertEqual(full_sync.status_code, 200)
        self.assertEqual(full_sync_payload["status"], "ok")

        pre_ws_response = self.client.get(reverse("simulator:ws_api_data"))
        pre_ws_payload = pre_ws_response.json()
        self.assertEqual(pre_ws_response.status_code, 200)
        self.assertIn("current", pre_ws_payload)
        self.assertIn("storage_drift", pre_ws_payload["current"])

        button1_response = self.client.post(reverse("simulator:ws_api_apply_balance"))
        button1_payload = button1_response.json()
        self.assertEqual(button1_response.status_code, 200)
        self.assertTrue(button1_payload["success"])
        self.assertLessEqual(abs(float(button1_payload.get("storage_drift") or 0.0)), 0.1)

        button2_response = self.client.post(reverse("simulator:ws_api_apply_full_balance"))
        button2_payload = button2_response.json()
        self.assertEqual(button2_response.status_code, 200)
        self.assertTrue(button2_payload["success"])
        self.assertIn("heat_balance", button2_payload)
        self.assertIn("after", button2_payload["heat_balance"])

        after = button2_payload["heat_balance"]["after"]
        self.assertLessEqual(abs(float(after["gebaeudewaerme"]["gap"])), 100.0)
        self.assertLessEqual(abs(float(after["prozesswaerme"]["gap"])), 100.0)
        self.assertLessEqual(abs(float(after["mobile_anwendungen"]["gap"])), 100.0)
        self.assertLessEqual(abs(float(button2_payload.get("storage_drift") or 0.0)), 0.1)
