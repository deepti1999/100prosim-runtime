from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from simulator.admin_roles import (
    user_can_edit_formula_master_data,
    user_can_edit_renewable_master_data,
)
from simulator.display_state import mark_display_state_changed
from simulator.models import Formula, FormulaVariable, RenewableData


VARIABLE_BLANK_ROWS = 3


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


def _target_formula_for_code(code):
    if not code:
        return None
    return Formula.objects.filter(
        category="renewable",
        key__in=[f"{code}_target", f"{code}_ziel_target", f"{code}_ziel"],
    ).order_by("key").first()


def _formula_by_key(key):
    key = (key or "").strip()
    if not key:
        return None
    return Formula.objects.filter(key=key, category="renewable").first()


def _save_formula_from_post(request, *, prefix, key, formula_type, fallback_description):
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
            "category": "renewable",
            "formula_type": formula_type,
            "expression": expression,
            "description": description or fallback_description,
            "is_active": is_active,
        },
    )
    formula.category = "renewable"
    formula.formula_type = formula_type
    formula.expression = expression
    formula.description = description or fallback_description
    formula.is_active = is_active
    formula.save()
    return formula


def _parse_optional_float(value):
    value = (value or "").strip()
    if not value:
        return None
    return _parse_float(value)


def _variables_for_template(formula):
    rows = []
    if formula:
        rows.extend(formula.variables.all())
    rows.extend({} for _ in range(VARIABLE_BLANK_ROWS))
    return rows


def _posted_variable_has_content(request, prefix, index):
    return any(
        (request.POST.get(f"{prefix}_var_{field}_{index}") or "").strip()
        for field in ("name", "source_type", "source_key", "default_value", "notes")
    )


def _save_variables_from_post(request, *, prefix, formula):
    if not user_can_edit_formula_master_data(request.user):
        return

    total = int(request.POST.get(f"{prefix}_variables_total") or 0)
    seen_names = set()

    for index in range(total):
        variable_id = (request.POST.get(f"{prefix}_var_id_{index}") or "").strip()
        variable_name = (request.POST.get(f"{prefix}_var_name_{index}") or "").strip()
        source_type = (request.POST.get(f"{prefix}_var_source_type_{index}") or "").strip()
        source_key = (request.POST.get(f"{prefix}_var_source_key_{index}") or "").strip()
        notes = (request.POST.get(f"{prefix}_var_notes_{index}") or "").strip()
        delete_requested = request.POST.get(f"{prefix}_var_delete_{index}") == "on"
        is_required = request.POST.get(f"{prefix}_var_is_required_{index}") == "on"

        existing = None
        if variable_id:
            existing = FormulaVariable.objects.filter(id=variable_id, formula=formula).first()

        if delete_requested:
            if existing:
                existing.delete()
            continue

        if not _posted_variable_has_content(request, prefix, index):
            continue

        if not formula:
            raise ValueError("Variablen brauchen zuerst eine gespeicherte Formel.")
        if not variable_name:
            raise ValueError("Jede Formel-Variable braucht einen Variablennamen.")
        if variable_name in seen_names:
            raise ValueError(f"Variable '{variable_name}' ist doppelt eingetragen.")
        seen_names.add(variable_name)
        if not source_type:
            raise ValueError(f"Variable '{variable_name}' braucht einen Quelltyp.")
        if source_type not in dict(FormulaVariable.SOURCE_CHOICES):
            raise ValueError(f"Variable '{variable_name}' hat einen unbekannten Quelltyp.")
        if not source_key:
            raise ValueError(f"Variable '{variable_name}' braucht einen Quellcode oder Wert.")

        default_value = _parse_optional_float(request.POST.get(f"{prefix}_var_default_value_{index}"))
        if existing is None:
            existing, _created = FormulaVariable.objects.get_or_create(
                formula=formula,
                variable_name=variable_name,
            )
        existing.variable_name = variable_name
        existing.source_type = source_type
        existing.source_key = source_key
        existing.default_value = default_value
        existing.is_required = is_required
        existing.notes = notes
        existing.save()


@login_required
def renewable_master_edit(request, pk):
    if not user_can_edit_renewable_master_data(request.user):
        raise PermissionDenied("Keine Berechtigung zum Bearbeiten von Erneuerbare-Stammdaten.")

    renewable = get_object_or_404(
        RenewableData.all_objects.select_related("region"),
        pk=pk,
    )

    status_formula_key = renewable.code or ""
    target_formula = _target_formula_for_code(renewable.code)
    target_formula_key = target_formula.key if target_formula else (f"{renewable.code}_target" if renewable.code else "")
    status_formula = _formula_by_key(status_formula_key)
    return_url = request.POST.get("return_url") or request.GET.get("return_url") or "simulator:renewable_list"

    if request.method == "POST":
        try:
            renewable.status_value = _parse_float(request.POST.get("status_value"))
            renewable.target_value = _parse_float(request.POST.get("target_value"))
            renewable.unit = (request.POST.get("unit") or "").strip()
            renewable.is_fixed = request.POST.get("is_fixed") == "on"
            renewable.user_editable = request.POST.get("user_editable") == "on"
            renewable.formula = (request.POST.get("row_formula") or "").strip() or None

            status_formula = _save_formula_from_post(
                request,
                prefix="status",
                key=status_formula_key,
                formula_type="status",
                fallback_description=f"Status-Formel für {renewable.code} {renewable.name}",
            )
            target_formula = _save_formula_from_post(
                request,
                prefix="target",
                key=target_formula_key,
                formula_type="ziel",
                fallback_description=f"Ziel-Formel für {renewable.code} {renewable.name}",
            )
            _save_variables_from_post(request, prefix="status", formula=status_formula)
            _save_variables_from_post(request, prefix="target", formula=target_formula)

            renewable.save()

            try:
                from simulator.recalc_cache import invalidate
                from simulator.recalc_service import recalc_all_renewables_full

                invalidate("recalc_all_renewables_full")
                updated_count = recalc_all_renewables_full()
                mark_display_state_changed(
                    scope="renewable_master_edit",
                    triggered_by=request.user.username,
                    model="RenewableData",
                    code=renewable.code,
                    region_code=renewable.region.code if renewable.region_id else "DE",
                    updated_count=updated_count,
                )
                messages.success(
                    request,
                    f"Erneuerbare-Werte und Formeln wurden gespeichert. {updated_count} berechnete Zeilen wurden aktualisiert.",
                )
            except Exception as exc:
                mark_display_state_changed(
                    scope="renewable_master_edit",
                    triggered_by=request.user.username,
                    model="RenewableData",
                    code=renewable.code,
                    region_code=renewable.region.code if renewable.region_id else "DE",
                    recalc_warning=str(exc),
                )
                messages.warning(
                    request,
                    f"Gespeichert, aber die automatische Neuberechnung konnte nicht vollständig laufen: {exc}",
                )

            if return_url.startswith("/"):
                return redirect(return_url)
            return redirect("simulator:renewable_list")
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(
        request,
        "simulator/renewable_master_edit.html",
        {
            "renewable": renewable,
            "status_formula": status_formula,
            "status_formula_key": status_formula_key,
            "target_formula": target_formula,
            "target_formula_key": target_formula_key,
            "status_variables": _variables_for_template(status_formula),
            "target_variables": _variables_for_template(target_formula),
            "formula_variable_source_choices": FormulaVariable.SOURCE_CHOICES,
            "return_url": return_url,
            "can_edit_formula_master_data": user_can_edit_formula_master_data(request.user),
            "current_section": "renewable",
        },
    )
