import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
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
            user_percent=44.0,
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

    def test_workspace_values_and_scenarios_are_available_to_logged_in_users(self):
        viewer = self._staff_user("viewer", "100ProSim Admin Viewer")
        editor = self._staff_user("editor", "100ProSim Admin Editor")
        normal = self.User.objects.create_user(username="normal", password="pass")

        self.assertTrue(user_can_edit_workspace_values(viewer))
        self.assertTrue(user_can_manage_workspace_scenarios(viewer))
        self.assertTrue(user_can_edit_workspace_values(editor))
        self.assertTrue(user_can_manage_workspace_scenarios(editor))
        self.assertTrue(user_can_edit_workspace_values(normal))
        self.assertTrue(user_can_manage_workspace_scenarios(normal))
        self.assertFalse(user_can_edit_workspace_values(AnonymousUser()))
        self.assertFalse(user_can_manage_workspace_scenarios(AnonymousUser()))

    def test_value_api_allows_staff_viewer_for_normal_workspace_inputs(self):
        viewer = self._staff_user("viewer_api", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": self.child.code, "user_percent": 10}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        viewer_child = LandUse.all_objects.get(
            owner=viewer,
            code=self.child.code,
            region=self.region,
        )
        self.assertEqual(viewer_child.user_percent, 10)
        self.child.refresh_from_db()
        self.assertEqual(self.child.user_percent, 44.0)

    def test_value_api_allows_staff_editor_for_normal_workspace_inputs(self):
        editor = self._staff_user("editor_api", "100ProSim Admin Editor")
        self.client.force_login(editor)
        recalc_cache._cache["stale-landuse-edit"] = (1, {"old": True})
        django_cache.set("stale-bilanz-landuse-edit", {"old": True}, timeout=60)

        response = self.client.post(
            reverse("simulator:update_user_percent"),
            data=json.dumps({"code": self.child.code, "user_percent": 10}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        editor_child = LandUse.all_objects.get(
            owner=editor,
            code=self.child.code,
            region=self.region,
        )
        self.assertEqual(editor_child.user_percent, 10)
        self.child.refresh_from_db()
        self.assertEqual(self.child.user_percent, 44.0)

    def test_renewable_value_api_allows_staff_editor_for_normal_workspace_inputs(self):
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

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        renewable = RenewableData.all_objects.get(
            owner=editor,
            code="ROLE_RE_1",
            region=self.region,
        )
        self.assertEqual(renewable.user_input, 33.5)
        global_renewable = RenewableData.all_objects.get(
            owner__isnull=True,
            code="ROLE_RE_1",
            region=self.region,
        )
        self.assertEqual(global_renewable.user_input, 20.0)

    def test_landuse_page_shows_normal_value_and_scenario_controls_to_staff_viewer(self):
        viewer = self._staff_user("viewer_page_values", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Werte-Bearbeitung aktiv")
        self.assertIn('<input type="number"', response.content.decode())
        self.assertIn('id="createScenarioBtn"', response.content.decode())

    def test_landuse_page_shows_normal_value_controls_but_not_master_editor_for_staff_editor(self):
        editor = self._staff_user("editor_page_values", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.get(reverse("simulator:landuse_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Werte-Bearbeitung aktiv")
        self.assertIn('<input type="number"', response.content.decode())
        self.assertNotContains(response, "Werte/Formel")
        self.assertContains(response, "Aktuelles Szenario speichern")

    def test_landuse_page_renders_unlocalized_value_input_ids(self):
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
        localized_clone = LandUse.all_objects.get(
            owner=editor,
            code="LU_LOCALIZED_ID",
            region=self.region,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'data-pk="{localized_clone.pk}"', html)
        self.assertIn(f'id="user_percent_{localized_clone.pk}"', html)
        self.assertNotIn('data-pk="1.000"', html)
        self.assertNotIn('id="user_percent_1.000"', html)

    def test_scenario_api_allows_staff_viewer_and_staff_editor_for_normal_ui_scenarios(self):
        viewer = self._staff_user("viewer_scenario", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        viewer_allowed = self.client.post(
            reverse("simulator:create_scenario"),
            data=json.dumps({"name": "Viewer scenario"}),
            content_type="application/json",
        )
        self.assertEqual(viewer_allowed.status_code, 200)
        self.assertEqual(viewer_allowed.json()["status"], "ok")

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
        self.assertEqual(scenario.owner, editor)
        self.assertEqual(
            next(row for row in scenario.payload["landuse"] if row["code"] == self.child.code)["user_percent"],
            44.0,
        )

        editor_child = LandUse.all_objects.get(
            owner=editor,
            code=self.child.code,
            region=self.region,
        )
        editor_child.user_percent = 99.0
        editor_child.save(update_fields=["user_percent"])
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
        restored_child = LandUse.all_objects.get(
            owner=editor,
            code=self.child.code,
            region=self.region,
        )
        self.assertEqual(restored_child.user_percent, 44.0)
        self.child.refresh_from_db()
        self.assertEqual(self.child.user_percent, 44.0)
