from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from simulator.admin_roles import (
    user_can_edit_formula_master_data,
    user_can_edit_landuse_master_data,
)
from simulator.display_state import mark_display_state_changed
from simulator.models import Formula, LandUse


def _parse_float(value):
    value = (value or "").strip()
    if not value:
        return None
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif "." in value:
        parts = value.split(".")
        if all(part.isdigit() for part in parts) and all(len(part) == 3 for part in parts[1:]):
            value = "".join(parts)
    if value.count(".") > 1:
        value = value.replace(".", "")
    return float(value)


def _formula_by_key(key):
    key = (key or "").strip()
    if not key:
        return None
    return Formula.objects.filter(key=key).first()


def _save_formula_from_post(request, *, prefix, key, fallback_description):
    key = (key or "").strip()
    expression = (request.POST.get(f"{prefix}_formula_expression") or "").strip()
    description = (request.POST.get(f"{prefix}_formula_description") or "").strip()
    is_active = request.POST.get(f"{prefix}_formula_is_active") == "on"

    if not key:
        if expression or description:
            raise ValueError("Eine Formel braucht zuerst einen Formel-Schlüssel.")
        return None

    if not user_can_edit_formula_master_data(request.user):
        return _formula_by_key(key)

    if not expression and not description:
        return _formula_by_key(key)

    formula, _created = Formula.objects.get_or_create(
        key=key,
        defaults={
            "category": "landuse",
            "formula_type": "status",
            "expression": expression,
            "description": description or fallback_description,
            "is_active": is_active,
        },
    )
    formula.category = "landuse"
    formula.expression = expression
    formula.description = description or fallback_description
    formula.is_active = is_active
    formula.save()
    return formula


@login_required
def landuse_master_edit(request, pk):
    if not user_can_edit_landuse_master_data(request.user):
        raise PermissionDenied("Keine Berechtigung zum Bearbeiten von Flächennutzungs-Stammdaten.")

    landuse = get_object_or_404(
        LandUse.all_objects.select_related("region", "parent"),
        pk=pk,
    )

    status_formula = _formula_by_key(landuse.status_formula_key)
    target_formula = _formula_by_key(landuse.target_formula_key)
    return_url = request.POST.get("return_url") or request.GET.get("return_url") or "simulator:landuse_list"

    if request.method == "POST":
        try:
            landuse.status_ha = _parse_float(request.POST.get("status_ha"))
            landuse.target_ha = _parse_float(request.POST.get("target_ha"))
            landuse.status_formula_key = (request.POST.get("status_formula_key") or "").strip() or None
            landuse.target_formula_key = (request.POST.get("target_formula_key") or "").strip() or None
            landuse.target_locked = request.POST.get("target_locked") == "on"

            status_formula = _save_formula_from_post(
                request,
                prefix="status",
                key=landuse.status_formula_key,
                fallback_description=f"Status-Formel für {landuse.code} {landuse.name}",
            )
            target_formula = _save_formula_from_post(
                request,
                prefix="target",
                key=landuse.target_formula_key,
                fallback_description=f"Ziel-Formel für {landuse.code} {landuse.name}",
            )
            if status_formula:
                landuse.status_formula_key = status_formula.key
            if target_formula:
                landuse.target_formula_key = target_formula.key

            landuse.save()
            mark_display_state_changed(
                scope="landuse_master_edit",
                triggered_by=request.user.username,
                model="LandUse",
                code=landuse.code,
                region_code=landuse.region.code if landuse.region_id else "DE",
            )
            messages.success(request, "Flächennutzungs-Werte und Formeln wurden gespeichert.")
            if return_url.startswith("/"):
                return redirect(return_url)
            return redirect("simulator:landuse_list")
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(
        request,
        "simulator/landuse_master_edit.html",
        {
            "landuse": landuse,
            "status_formula": status_formula,
            "target_formula": target_formula,
            "return_url": return_url,
            "can_edit_formula_master_data": user_can_edit_formula_master_data(request.user),
            "current_section": "landuse",
        },
    )
