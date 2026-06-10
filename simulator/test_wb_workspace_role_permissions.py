import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache as django_cache
from django.test import TestCase
from django.urls import reverse

from simulator import recalc_cache
from simulator.admin_roles import (
    ensure_admin_role_groups,
    user_can_edit_workspace_values,
    user_can_manage_workspace_scenarios,
)
from simulator.models import CalculationRun, GebaeudewaermeData, LandUse, Region, RenewableData, ScenarioSnapshot


class WorkspaceRolePermissionTests(TestCase):
    def setUp(self):
        ensure_admin_role_groups()
        self.User = get_user_model()
        self.region = Region.objects.get(code="DE")
        self.parent = LandUse.objects.create(
            code="LU_PARENT",
            name="Parent",
            region=self.region,
            status_ha=1000.0,
            target_ha=1000.0,
        )
        self.child = LandUse.objects.create(
            code="LU_CHILD",
            name="Child",
            region=self.region,
            parent=self.parent,
            status_ha=100.0,
            target_ha=100.0,
        )
        self.building_heat = GebaeudewaermeData.objects.create(
            code="GW_TEST",
            category="Gebäudewärme Test",
            unit="%",
            region=self.region,
            status=12.0,
            ziel=20.0,
            user_percent=44.0,
        )

    def _staff_user(self, username, role_name):
        user = self.User.objects.create_user(
            username=username,
            password="pass",
            is_staff=True,
        )
        user.groups.add(Group.objects.get(name=role_name))
        return user

    def test_ui_value_editing_is_disabled_but_scenarios_stay_available(self):
        viewer = self._staff_user("viewer", "100ProSim Admin Viewer")
        editor = self._staff_user("editor", "100ProSim Admin Editor")
        normal = self.User.objects.create_user(username="normal", password="pass")

        self.assertFalse(user_can_edit_workspace_values(viewer))
        self.assertFalse(user_can_manage_workspace_scenarios(viewer))
        self.assertFalse(user_can_edit_workspace_values(editor))
        self.assertTrue(user_can_manage_workspace_scenarios(editor))
        self.assertFalse(user_can_edit_workspace_values(normal))
        self.assertTrue(user_can_manage_workspace_scenarios(normal))

    def test_value_api_rejects_staff_viewer(self):
        viewer = self._staff_user("viewer_api", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": self.child.code, "user_percent": 10}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])

    def test_value_api_rejects_staff_editor(self):
        editor = self._staff_user("editor_api", "100ProSim Admin Editor")
        self.client.force_login(editor)
        recalc_cache._cache["stale-landuse-edit"] = (1, {"old": True})
        django_cache.set("stale-bilanz-landuse-edit", {"old": True}, timeout=60)

        response = self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": self.child.code, "user_percent": 10}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])
        self.child.refresh_from_db()
        self.assertIsNone(self.child.user_percent)
        self.assertIn("stale-landuse-edit", recalc_cache._cache)
        self.assertIsNotNone(django_cache.get("stale-bilanz-landuse-edit"))

    def test_renewable_value_api_rejects_staff_editor(self):
        RenewableData.objects.create(
            code="ROLE_RE_1",
            name="Editable renewable input",
            category="renewable",
            region=self.region,
            unit="GWh/a",
            status_value=10.0,
            target_value=20.0,
            user_input=20.0,
            is_fixed=True,
            user_editable=True,
        )
        editor = self._staff_user("editor_renewable_api", "100ProSim Admin Editor")
        self.client.force_login(editor)
        recalc_cache._cache["stale-renewable-edit"] = (1, {"old": True})
        django_cache.set("stale-bilanz-renewable-edit", {"old": True}, timeout=60)

        response = self.client.post(
            reverse("simulator:save_renewable_user_input"),
            data=json.dumps({"code": "ROLE_RE_1", "user_input": 33.5}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])
        self.assertIn("stale-renewable-edit", recalc_cache._cache)
        self.assertIsNotNone(django_cache.get("stale-bilanz-renewable-edit"))

    def test_landuse_page_hides_value_and_scenario_controls_from_staff_viewer(self):
        viewer = self._staff_user("viewer_page_values", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nur ansehen")
        self.assertNotIn('<input type="number"', response.content.decode())
        self.assertNotIn('id="createScenarioBtn"', response.content.decode())

    def test_landuse_page_hides_value_controls_but_keeps_scenario_controls_for_staff_editor(self):
        editor = self._staff_user("editor_page_values", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Werte-Bearbeitung aktiv")
        self.assertNotIn('<input type="number"', response.content.decode())
        self.assertNotContains(response, "Werte/Formel")
        self.assertContains(response, "Aktuelles Szenario speichern")

    def test_landuse_page_does_not_render_ui_value_save_inputs(self):
        LandUse.objects.create(
            id=1000,
            code="LU_LOCALIZED_ID",
            name="Localized id guard",
            region=self.region,
            parent=self.parent,
            status_ha=10.0,
            target_ha=10.0,
        )
        editor = self._staff_user("editor_localized_id", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.get(reverse("simulator:landuse_list"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('data-pk="1000"', html)
        self.assertNotIn('id="user_percent_1000"', html)
        self.assertNotIn('data-pk="1.000"', html)
        self.assertNotIn('id="user_percent_1.000"', html)

    def test_scenario_api_rejects_staff_viewer_and_allows_staff_editor(self):
        viewer = self._staff_user("viewer_scenario", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        blocked = self.client.post(
            reverse("simulator:create_scenario"),
            data=json.dumps({"name": "Viewer scenario"}),
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 403)

        editor = self._staff_user("editor_scenario", "100ProSim Admin Editor")
        self.client.force_login(editor)

        allowed = self.client.post(
            reverse("simulator:create_scenario"),
            data=json.dumps({"name": "Editor scenario"}),
            content_type="application/json",
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["status"], "ok")
        scenario = ScenarioSnapshot.objects.get(name="Editor scenario")
        self.assertEqual(
            scenario.payload["gebaeudewaerme"][0]["code"],
            self.building_heat.code,
        )

        self.building_heat.user_percent = 99.0
        self.building_heat.save(update_fields=["user_percent"])
        recalc_cache._cache["stale-test"] = (1, {"old": True})
        django_cache.set("stale-bilanz-test", {"old": True}, timeout=60)
        restored = self.client.post(reverse("simulator:restore_scenario", args=[scenario.id]))
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(recalc_cache._cache, {})
        self.assertIsNone(django_cache.get("stale-bilanz-test"))
        run = CalculationRun.objects.latest("id")
        self.assertEqual(run.summary["scope"], "snapshot_restore")
        self.assertEqual(run.summary["restore_type"], "scenario")
        self.assertEqual(run.summary["snapshot_name"], "Editor scenario")
        restored_building_heat = GebaeudewaermeData.all_objects.get(
            code=self.building_heat.code,
            region=self.region,
        )
        self.assertEqual(restored_building_heat.user_percent, 44.0)
