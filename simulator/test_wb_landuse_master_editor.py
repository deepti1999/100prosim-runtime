from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache as django_cache
from django.test import TestCase
from django.urls import reverse

from simulator import recalc_cache
from simulator.admin_roles import ensure_admin_role_groups
from simulator.models import CalculationRun, Formula, LandUse, Region


class LandUseMasterEditorTests(TestCase):
    def setUp(self):
        ensure_admin_role_groups()
        self.User = get_user_model()
        self.region = Region.objects.get(code="DE")
        self.landuse = LandUse.objects.create(
            code="LU_EDIT",
            name="Editierbare Testfläche",
            region=self.region,
            status_ha=100.0,
            target_ha=200.0,
            status_formula_key="LANDUSE_EDIT_STATUS",
            target_formula_key="LANDUSE_EDIT_TARGET",
        )
        Formula.objects.create(
            key="LANDUSE_EDIT_STATUS",
            category="landuse",
            expression="100",
            description="Old status formula",
            is_active=True,
        )
        Formula.objects.create(
            key="LANDUSE_EDIT_TARGET",
            category="landuse",
            expression="200",
            description="Old target formula",
            is_active=True,
        )

    def _staff_user(self, username, role_name):
        user = self.User.objects.create_user(
            username=username,
            password="pass",
            is_staff=True,
        )
        user.groups.add(Group.objects.get(name=role_name))
        return user

    def test_normal_user_cannot_open_landuse_master_editor(self):
        user = self.User.objects.create_user(username="normal_landuse_editor", password="pass")
        self.client.force_login(user)

        response = self.client.get(
            reverse("simulator:landuse_master_edit", args=[self.landuse.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_viewer_cannot_open_landuse_master_editor(self):
        viewer = self._staff_user("viewer_landuse_editor", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(
            reverse("simulator:landuse_master_edit", args=[self.landuse.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_editor_cannot_open_landuse_master_editor_from_table(self):
        editor = self._staff_user("editor_landuse_table", "100ProSim Admin Editor")
        self.client.force_login(editor)

        table = self.client.get(reverse("simulator:landuse_list"))
        edit = self.client.get(reverse("simulator:landuse_master_edit", args=[self.landuse.id]))

        self.assertNotContains(table, "Werte/Formel")
        self.assertEqual(edit.status_code, 403)

    def test_staff_editor_cannot_update_landuse_values_and_formula_text_from_ui(self):
        editor = self._staff_user("editor_landuse_save", "100ProSim Admin Editor")
        self.client.force_login(editor)
        recalc_cache._cache["stale-landuse-master"] = (1, {"old": True})
        django_cache.set("stale-bilanz-master", {"old": True}, timeout=60)

        response = self.client.post(
            reverse("simulator:landuse_master_edit", args=[self.landuse.id]),
            data={
                "status_ha": "1234",
                "target_ha": "5678",
                "status_formula_key": "LANDUSE_EDIT_STATUS",
                "target_formula_key": "LANDUSE_EDIT_TARGET",
                "target_locked": "on",
                "status_formula_expression": "1234",
                "status_formula_description": "New status formula",
                "status_formula_is_active": "on",
                "target_formula_expression": "5678",
                "target_formula_description": "New target formula",
                "target_formula_is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.landuse.refresh_from_db()
        self.assertEqual(self.landuse.status_ha, 100.0)
        self.assertEqual(self.landuse.target_ha, 200.0)
        self.assertFalse(self.landuse.target_locked)
        self.assertEqual(
            Formula.objects.get(key="LANDUSE_EDIT_STATUS").expression,
            "100",
        )
        self.assertEqual(
            Formula.objects.get(key="LANDUSE_EDIT_TARGET").description,
            "Old target formula",
        )
        self.assertIn("stale-landuse-master", recalc_cache._cache)
        self.assertIsNotNone(django_cache.get("stale-bilanz-master"))

    def test_staff_editor_cannot_save_german_thousands_format_from_ui(self):
        editor = self._staff_user("editor_landuse_german_number", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.post(
            reverse("simulator:landuse_master_edit", args=[self.landuse.id]),
            data={
                "status_ha": "34.450",
                "target_ha": "199.680",
                "status_formula_key": "",
                "target_formula_key": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.landuse.refresh_from_db()
        self.assertEqual(self.landuse.status_ha, 100.0)
        self.assertEqual(self.landuse.target_ha, 200.0)
