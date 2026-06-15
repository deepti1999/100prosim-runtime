from __future__ import annotations

from django.apps import apps as django_apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate


ADMIN_FULL_GROUP = "100ProSim Admin Full"


ROLE_GROUPS = {
    "100ProSim Admin Viewer": {
        "description": "Can open admin and view data, but not change it.",
        "levels": ["view"],
        "custom": [],
        "delete_models": [],
    },
    "100ProSim Admin Editor": {
        "description": "Can edit admin data and create/update draft versions.",
        "levels": ["view", "add", "change"],
        "custom": ["refresh_admin_data_version"],
        "delete_models": [],
    },
    "100ProSim Admin Manager": {
        "description": "Can edit, restore saved versions, protect versions, and delete saved admin scenarios.",
        "levels": ["view", "add", "change"],
        "custom": [
            "refresh_admin_data_version",
            "restore_admin_data_version",
            "protect_admin_data_version",
        ],
        "delete_models": ["AdminDataVersion"],
    },
    ADMIN_FULL_GROUP: {
        "description": "Can fully manage the 100ProSim admin data models and assign admin roles.",
        "levels": ["view", "add", "change", "delete"],
        "custom": [
            "refresh_admin_data_version",
            "restore_admin_data_version",
            "protect_admin_data_version",
        ],
        "auth_levels": ["view", "add", "change"],
    },
}


ROLE_MODEL_NAMES = [
    "AdminDataVersion",
    "UIProvenanceOverride",
    "UIProvenanceSource",
    "LandUse",
    "RenewableData",
    "VerbrauchData",
    "GebaeudewaermeData",
    "Formula",
    "FormulaVariable",
    "WSData",
    "WS365Formula",
    "Region",
    "CategoryDisplayName",
]

AUTH_ROLE_MODEL_NAMES = [
    "User",
    "Group",
]


def _model_permissions(model, levels):
    content_type = ContentType.objects.get_for_model(model)
    model_name = model._meta.model_name
    codenames = [f"{level}_{model_name}" for level in levels]
    return list(Permission.objects.filter(content_type=content_type, codename__in=codenames))


def _custom_permissions(codenames):
    if not codenames:
        return []
    model = django_apps.get_model("simulator", "AdminDataVersion")
    content_type = ContentType.objects.get_for_model(model)
    return list(Permission.objects.filter(content_type=content_type, codename__in=codenames))


def _auth_permissions(levels):
    permissions = []
    for model_name in AUTH_ROLE_MODEL_NAMES:
        model = django_apps.get_model("auth", model_name)
        permissions.extend(_model_permissions(model, levels))
    return permissions


def user_can_manage_admin_roles(user) -> bool:
    """Only the real top-level admin role may create users or assign roles."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=ADMIN_FULL_GROUP).exists()


def user_can_edit_ui_provenance(user) -> bool:
    """Allow trusted content editors to edit UI-only source/explanation text."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.has_perm("simulator.change_uiprovenanceoverride")


def user_can_edit_landuse_master_data(user) -> bool:
    """Master values are editable in Django admin only, not in the normal UI."""
    return False


def user_can_edit_renewable_master_data(user) -> bool:
    """Master values are editable in Django admin only, not in the normal UI."""
    return False


def user_can_edit_formula_master_data(user) -> bool:
    """Formula expressions are editable in Django admin only, not in the normal UI."""
    return False


def user_can_edit_workspace_values(user) -> bool:
    """Normal scenario/workspace inputs are editable by every logged-in user."""
    return bool(getattr(user, "is_authenticated", False))


def user_can_manage_workspace_scenarios(user) -> bool:
    """Normal UI scenarios are part of each logged-in user's workspace."""
    return bool(getattr(user, "is_authenticated", False))


def ensure_admin_role_groups(sender=None, **kwargs):
    """Create/update simple admin role groups after migrations.

    Users still need `is_staff=True` to enter Django admin. These groups
    then decide what they can view, edit, refresh, restore, or delete.
    """
    permissions_by_role = {}
    for group_name, config in ROLE_GROUPS.items():
        permissions = []
        for model_name in ROLE_MODEL_NAMES:
            try:
                model = django_apps.get_model("simulator", model_name)
            except LookupError:
                continue
            permissions.extend(_model_permissions(model, config["levels"]))
        for model_name in config.get("delete_models", []):
            try:
                model = django_apps.get_model("simulator", model_name)
            except LookupError:
                continue
            permissions.extend(_model_permissions(model, ["delete"]))
        permissions.extend(_custom_permissions(config["custom"]))
        permissions.extend(_auth_permissions(config.get("auth_levels", [])))
        permissions_by_role[group_name] = permissions

    for group_name, permissions in permissions_by_role.items():
        group, _created = Group.objects.get_or_create(name=group_name)
        group.permissions.set(permissions)


def connect_admin_role_groups(app_config):
    post_migrate.connect(
        ensure_admin_role_groups,
        sender=app_config,
        dispatch_uid="simulator.ensure_admin_role_groups",
    )
