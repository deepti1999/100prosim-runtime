from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache as django_cache
from django.test import TestCase
from django.urls import reverse

from simulator import recalc_cache
from simulator.admin_roles import ensure_admin_role_groups
from simulator.models import CalculationRun, Formula, FormulaVariable, Region, RenewableData


class RenewableMasterEditorTests(TestCase):
    def setUp(self):
        ensure_admin_role_groups()
        self.User = get_user_model()
        self.region = Region.objects.get(code="DE")
        self.renewable = RenewableData.objects.create(
            category="Solarenergie",
            subcategory="Test",
            code="R_EDIT",
            name="Editierbare Erneuerbare",
            unit="GWh/a",
            status_value=100.0,
            target_value=200.0,
            is_fixed=True,
            user_editable=True,
            formula="old row formula",
            region=self.region,
        )
        self.status_formula = Formula.objects.create(
            key="R_EDIT",
            category="renewable",
            formula_type="status",
            expression="100",
            description="Old renewable status formula",
            is_active=True,
        )
        self.target_formula = Formula.objects.create(
            key="R_EDIT_target",
            category="renewable",
            formula_type="ziel",
            expression="200",
            description="Old renewable target formula",
            is_active=True,
        )
        FormulaVariable.objects.create(
            formula=self.target_formula,
            variable_name="existing_status_input",
            source_type=FormulaVariable.RENEWABLE_STATUS,
            source_key="R_EDIT",
            default_value=0,
            notes="Uses status value in target formula",
        )

    def _staff_user(self, username, role_name):
        user = self.User.objects.create_user(
            username=username,
            password="pass",
            is_staff=True,
        )
        user.groups.add(Group.objects.get(name=role_name))
        return user

    def test_normal_user_cannot_open_renewable_master_editor(self):
        user = self.User.objects.create_user(username="normal_renewable_editor", password="pass")
        self.client.force_login(user)

        response = self.client.get(
            reverse("simulator:renewable_master_edit", args=[self.renewable.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_viewer_cannot_open_renewable_master_editor(self):
        viewer = self._staff_user("viewer_renewable_editor", "100ProSim Admin Viewer")
        self.client.force_login(viewer)

        response = self.client.get(
            reverse("simulator:renewable_master_edit", args=[self.renewable.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_editor_cannot_open_renewable_master_editor_from_table(self):
        editor = self._staff_user("editor_renewable_table", "100ProSim Admin Editor")
        self.client.force_login(editor)

        table = self.client.get(reverse("simulator:renewable_list"))
        edit = self.client.get(reverse("simulator:renewable_master_edit", args=[self.renewable.id]))

        self.assertNotContains(table, "Werte/Formel")
        self.assertEqual(edit.status_code, 403)

    def test_staff_editor_cannot_update_renewable_values_and_formula_text_from_ui(self):
        editor = self._staff_user("editor_renewable_save", "100ProSim Admin Editor")
        self.client.force_login(editor)
        recalc_cache._cache["stale-renewable-master"] = (1, {"old": True})
        django_cache.set("stale-bilanz-renewable-master", {"old": True}, timeout=60)

        response = self.client.post(
            reverse("simulator:renewable_master_edit", args=[self.renewable.id]),
            data={
                "status_value": "1234",
                "target_value": "5678",
                "unit": "MWh/a",
                "is_fixed": "on",
                "user_editable": "on",
                "row_formula": "new row formula",
                "status_formula_expression": "1234",
                "status_formula_description": "New renewable status formula",
                "status_formula_is_active": "on",
                "target_formula_expression": "5678",
                "target_formula_description": "New renewable target formula",
                "target_formula_is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.renewable.refresh_from_db()
        self.assertEqual(self.renewable.status_value, 100.0)
        self.assertEqual(self.renewable.target_value, 200.0)
        self.assertEqual(self.renewable.unit, "GWh/a")
        self.assertEqual(self.renewable.formula, "old row formula")
        self.assertTrue(self.renewable.is_fixed)
        self.assertTrue(self.renewable.user_editable)
        self.assertEqual(
            Formula.objects.get(key="R_EDIT").expression,
            "100",
        )
        self.assertEqual(
            Formula.objects.get(key="R_EDIT_target").description,
            "Old renewable target formula",
        )
        self.assertIn("stale-renewable-master", recalc_cache._cache)
        self.assertIsNotNone(django_cache.get("stale-bilanz-renewable-master"))

    def test_staff_editor_cannot_save_german_thousands_format_from_ui(self):
        editor = self._staff_user("editor_renewable_german_number", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.post(
            reverse("simulator:renewable_master_edit", args=[self.renewable.id]),
            data={
                "status_value": "34.450,5",
                "target_value": "199.680",
                "unit": "GWh/a",
                "is_fixed": "on",
                "row_formula": "",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.renewable.refresh_from_db()
        self.assertEqual(self.renewable.status_value, 100.0)
        self.assertEqual(self.renewable.target_value, 200.0)

    def test_staff_editor_cannot_map_target_formula_variable_from_ui(self):
        editor = self._staff_user("editor_renewable_variable", "100ProSim Admin Editor")
        self.client.force_login(editor)

        response = self.client.post(
            reverse("simulator:renewable_master_edit", args=[self.renewable.id]),
            data={
                "status_value": "100",
                "target_value": "200",
                "unit": "GWh/a",
                "is_fixed": "on",
                "user_editable": "on",
                "row_formula": "variable mapping test",
                "status_formula_expression": "100",
                "status_formula_description": "Status formula",
                "status_formula_is_active": "on",
                "status_variables_total": "0",
                "target_formula_expression": "status_for_target * 2",
                "target_formula_description": "Target formula using status source",
                "target_formula_is_active": "on",
                "target_variables_total": "1",
                "target_var_name_0": "status_for_target",
                "target_var_source_type_0": FormulaVariable.RENEWABLE_STATUS,
                "target_var_source_key_0": "R_EDIT",
                "target_var_default_value_0": "0",
                "target_var_is_required_0": "on",
                "target_var_notes_0": "Ziel formula intentionally reads status.",
            },
        )

        self.assertEqual(response.status_code, 403)
        variable = FormulaVariable.objects.get(
            formula__key="R_EDIT_target",
            variable_name="existing_status_input",
        )
        self.assertEqual(variable.source_type, FormulaVariable.RENEWABLE_STATUS)
        self.assertEqual(variable.source_key, "R_EDIT")
        self.assertEqual(variable.default_value, 0)
        self.assertIn("status value", variable.notes)
