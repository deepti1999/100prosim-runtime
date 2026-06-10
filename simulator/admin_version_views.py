from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from simulator.admin_versioning import (
    capture_admin_version_payload,
    payload_size_mb,
    restore_admin_version_payload,
)
from simulator.models import AdminDataVersion, Region


@login_required
@permission_required("simulator.view_admindataversion", raise_exception=True)
def admin_versions_dashboard(request):
    versions = (
        AdminDataVersion.objects.select_related("region", "created_by")
        .order_by("-captured_at", "-updated_at")
    )
    return render(
        request,
        "simulator/admin_versions/dashboard.html",
        {
            "versions": versions,
            "can_add_version": request.user.has_perm("simulator.add_admindataversion"),
            "can_restore_version": request.user.has_perm("simulator.restore_admin_data_version"),
            "can_refresh_version": request.user.has_perm("simulator.refresh_admin_data_version"),
            "can_delete_version": request.user.has_perm("simulator.delete_admindataversion"),
        },
    )


@login_required
@permission_required("simulator.add_admindataversion", raise_exception=True)
def admin_version_create(request):
    regions = Region.objects.filter(active=True).order_by("code")
    default_name = timezone.localtime().strftime("Admin-Szenario %d.%m.%Y %H:%M")
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        note = (request.POST.get("note") or "").strip()
        region_code = (request.POST.get("region") or "DE").strip()
        status = request.POST.get("status") or AdminDataVersion.STATUS_DRAFT
        is_protected = bool(request.POST.get("is_protected"))

        if not name:
            messages.error(request, "Bitte einen Versionsnamen eingeben.")
        elif AdminDataVersion.objects.filter(region__code=region_code, name=name).exists():
            messages.error(request, "Für diese Region gibt es bereits eine Version mit diesem Namen.")
        else:
            region = get_object_or_404(Region, code=region_code, active=True)
            version = AdminDataVersion.objects.create(
                region=region,
                name=name,
                note=note,
                status=status,
                is_protected=is_protected,
                created_by=request.user,
                payload=capture_admin_version_payload(region.code),
                captured_at=timezone.now(),
            )
            messages.success(
                request,
                f'Admin-Szenario "{version.name}" wurde gespeichert.',
            )
            return redirect("simulator:admin_versions_dashboard")

    return render(
        request,
        "simulator/admin_versions/create.html",
        {
            "regions": regions,
            "status_choices": AdminDataVersion.STATUS_CHOICES,
            "default_name": default_name,
        },
    )


@login_required
@permission_required("simulator.restore_admin_data_version", raise_exception=True)
def admin_version_restore(request, version_id):
    version = get_object_or_404(AdminDataVersion, pk=version_id)
    counts = (version.payload or {}).get("counts") or {}
    if request.method == "POST":
        restored = restore_admin_version_payload(version.payload)
        details = ", ".join(f"{key}: {value}" for key, value in restored.items())
        messages.success(
            request,
            f'Admin-Szenario "{version.name}" wurde wiederhergestellt. {details}',
        )
        return redirect("simulator:admin_versions_dashboard")

    return render(
        request,
        "simulator/admin_versions/restore.html",
        {
            "version": version,
            "counts": counts,
            "payload_size": payload_size_mb(version.payload),
        },
    )


@login_required
@permission_required("simulator.refresh_admin_data_version", raise_exception=True)
def admin_version_refresh(request, version_id):
    version = get_object_or_404(AdminDataVersion, pk=version_id)
    if version.is_protected:
        messages.error(request, "Geschützte Versionen können nicht überschrieben werden.")
        return redirect("simulator:admin_versions_dashboard")

    if request.method == "POST":
        version.payload = capture_admin_version_payload(version.region.code)
        version.captured_at = timezone.now()
        version.save(update_fields=["payload", "captured_at", "updated_at"])
        messages.success(
            request,
            f'Admin-Szenario "{version.name}" wurde mit dem aktuellen Stand neu gespeichert.',
        )
        return redirect("simulator:admin_versions_dashboard")

    return render(
        request,
        "simulator/admin_versions/refresh.html",
        {"version": version},
    )


@login_required
@permission_required("simulator.delete_admindataversion", raise_exception=True)
def admin_version_delete(request, version_id):
    version = get_object_or_404(AdminDataVersion, pk=version_id)
    if version.is_protected:
        messages.error(request, "Geschützte Admin-Szenarien können nicht gelöscht werden.")
        return redirect("simulator:admin_versions_dashboard")

    if request.method == "POST":
        name = version.name
        version.delete()
        messages.success(request, f'Admin-Szenario "{name}" wurde gelöscht.')
        return redirect("simulator:admin_versions_dashboard")

    return render(
        request,
        "simulator/admin_versions/delete.html",
        {"version": version},
    )
