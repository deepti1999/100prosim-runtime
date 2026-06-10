from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from simulator.admin_roles import (
    ADMIN_FULL_GROUP,
    ensure_admin_role_groups,
    user_can_manage_admin_roles,
)


class AdminRoleAccessTests(TestCase):
    def setUp(self):
        ensure_admin_role_groups()
        self.User = get_user_model()

    def _staff_user(self, username, role_name):
        user = self.User.objects.create_user(
            username=username,
            password="pass",
            is_staff=True,
        )
        user.groups.add(Group.objects.get(name=role_name))
        return user

    def test_full_role_gets_user_and_group_management_permissions(self):
        full_group = Group.objects.get(name=ADMIN_FULL_GROUP)
        codenames = set(full_group.permissions.values_list("codename", flat=True))

        self.assertIn("view_user", codenames)
        self.assertIn("add_user", codenames)
        self.assertIn("change_user", codenames)
        self.assertIn("view_group", codenames)
        self.assertIn("change_group", codenames)

    def test_only_full_role_or_superuser_can_manage_admin_roles(self):
        manager = self._staff_user("manager", "100ProSim Admin Manager")
        full_admin = self._staff_user("fulladmin", ADMIN_FULL_GROUP)
        superuser = self.User.objects.create_superuser(
            username="root",
            password="pass",
        )

        self.assertFalse(user_can_manage_admin_roles(manager))
        self.assertTrue(user_can_manage_admin_roles(full_admin))
        self.assertTrue(user_can_manage_admin_roles(superuser))

    def test_manager_cannot_open_role_assignment_pages(self):
        manager = self._staff_user("manager", "100ProSim Admin Manager")
        self.client.force_login(manager)

        for url_name in ("simulator:admin_roles_dashboard", "simulator:admin_role_assign"):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 403)

    def test_full_admin_can_assign_role_to_normal_user(self):
        full_admin = self._staff_user("fulladmin", ADMIN_FULL_GROUP)
        target = self.User.objects.create_user(
            username="editor_target",
            password="pass",
            is_staff=False,
            is_active=False,
        )
        self.client.force_login(full_admin)

        response = self.client.post(
            reverse("simulator:admin_role_assign"),
            {
                "user": target.pk,
                "role": "100ProSim Admin Editor",
            },
        )

        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        self.assertTrue(target.is_staff)
        self.assertTrue(
            target.groups.filter(name="100ProSim Admin Editor").exists()
        )

    def test_role_assignment_page_links_to_password_change(self):
        full_admin = self._staff_user("fulladmin", ADMIN_FULL_GROUP)
        target = self.User.objects.create_user(
            username="kiran",
            password="pass",
            is_staff=True,
        )
        self.client.force_login(full_admin)

        response = self.client.get(reverse("simulator:admin_role_assign"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwort setzen")
        self.assertContains(
            response,
            reverse("admin:auth_user_password_change", args=[target.pk]),
        )
