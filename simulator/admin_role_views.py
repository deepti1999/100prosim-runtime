from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse

from simulator.admin_roles import (
    ROLE_GROUPS,
    ensure_admin_role_groups,
    user_can_manage_admin_roles,
)


ROLE_GUIDE = [
    {
        "name": "100ProSim Admin Viewer",
        "label": "Nur ansehen",
        "summary": "Kann Admin-Daten ansehen, aber nichts ändern.",
        "best_for": "Personen, die prüfen oder nachschauen sollen.",
    },
    {
        "name": "100ProSim Admin Editor",
        "label": "Bearbeiten",
        "summary": "Kann Werte, Formeln und Quellen bearbeiten und Admin-Szenarien speichern.",
        "best_for": "Personen, die Inhalte pflegen, aber nichts zurücksetzen sollen.",
    },
    {
        "name": "100ProSim Admin Manager",
        "label": "Manager",
        "summary": "Kann bearbeiten, Admin-Szenarien speichern, wiederherstellen, schützen und löschen.",
        "best_for": "Verantwortliche Personen, die Änderungen kontrollieren.",
    },
    {
        "name": "100ProSim Admin Full",
        "label": "Vollzugriff",
        "summary": "Kann alles verwalten, inklusive Löschen von normalen Admin-Daten.",
        "best_for": "Nur technische Hauptverantwortliche.",
    },
]


@login_required
def admin_roles_dashboard(request):
    if not user_can_manage_admin_roles(request.user):
        raise PermissionDenied
    return render(
        request,
        "simulator/admin_roles/dashboard.html",
        {
            "roles": ROLE_GUIDE,
            "users_url": reverse("admin:auth_user_changelist"),
            "groups_url": reverse("admin:auth_group_changelist"),
            "assign_url": reverse("simulator:admin_role_assign"),
        },
    )


@login_required
def admin_role_assign(request):
    if not user_can_manage_admin_roles(request.user):
        raise PermissionDenied
    ensure_admin_role_groups()
    User = get_user_model()
    role_names = list(ROLE_GROUPS.keys())
    users = (
        User.objects.filter(is_superuser=False)
        .order_by("username")
        .prefetch_related("groups")
    )

    if request.method == "POST":
        user_id = request.POST.get("user")
        role_name = request.POST.get("role")
        if role_name not in role_names:
            messages.error(request, "Bitte eine gültige 100ProSim-Rolle auswählen.")
        else:
            user = User.objects.filter(pk=user_id, is_superuser=False).first()
            if not user:
                messages.error(request, "Bitte einen gültigen Nutzer auswählen.")
            else:
                role_group = Group.objects.get(name=role_name)
                old_roles = Group.objects.filter(name__in=role_names)
                user.groups.remove(*old_roles)
                user.groups.add(role_group)
                fields_to_update = []
                if not user.is_active:
                    user.is_active = True
                    fields_to_update.append("is_active")
                if not user.is_staff:
                    user.is_staff = True
                    fields_to_update.append("is_staff")
                if fields_to_update:
                    user.save(update_fields=fields_to_update)
                messages.success(
                    request,
                    f'{user.get_username()} hat jetzt die Rolle "{role_name}".',
                )
                return redirect("simulator:admin_roles_dashboard")

    user_rows = []
    for user in users:
        current_roles = [group.name for group in user.groups.all() if group.name in role_names]
        user_rows.append(
            {
                "user": user,
                "role": current_roles[0] if current_roles else "Noch keine 100ProSim-Rolle",
                "admin_ready": user.is_active and user.is_staff and user.has_usable_password(),
                "password_url": reverse("admin:auth_user_password_change", args=[user.pk]),
            }
        )

    return render(
        request,
        "simulator/admin_roles/assign.html",
        {
            "roles": ROLE_GUIDE,
            "role_names": role_names,
            "users": users,
            "user_rows": user_rows,
        },
    )
