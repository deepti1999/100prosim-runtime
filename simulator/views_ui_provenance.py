from __future__ import annotations

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from simulator.admin_roles import user_can_edit_ui_provenance
from simulator.models import (
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    UIProvenanceOverride,
    UIProvenanceSource,
    VerbrauchData,
)
from simulator.region_scope import get_current_region_code
from simulator.ui_provenance_service import split_notes_assumption_sections


DOMAIN_MODEL_MAP = {
    "landuse": (LandUse, "name"),
    "renewable": (RenewableData, "name"),
    "verbrauch": (VerbrauchData, "category"),
    "gebaeudewaerme": (GebaeudewaermeData, "category"),
}


class UIProvenanceEditorForm(forms.Form):
    general_information = forms.CharField(
        label="Zusätzliche Information",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
    status_information = forms.CharField(
        label="Status-Erklärung",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
    )
    ziel_information = forms.CharField(
        label="Ziel-Erklärung",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
    )
    is_active = forms.BooleanField(
        label="Aktiv anzeigen",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class UIProvenanceSourceForm(forms.Form):
    section = forms.ChoiceField(
        label="Bereich",
        choices=[
            ("general", "Allgemein"),
            ("status", "Status"),
            ("ziel", "Ziel"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    label = forms.CharField(
        label="Kurztitel",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        label="Quellenbeschreibung",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
    url = forms.URLField(
        label="Link",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    sort_order = forms.IntegerField(
        label="Reihenfolge",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


SourceFormSet = formset_factory(
    UIProvenanceSourceForm,
    extra=2,
    max_num=8,
    validate_max=True,
    can_delete=True,
)


def _safe_return_url(request):
    candidate = request.POST.get("return_url") or request.GET.get("return_url") or ""
    if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return reverse("simulator:data_sources")


def _active_region_for_request(request):
    region_id = request.GET.get("region_id") or request.POST.get("region_id")
    if region_id:
        return get_object_or_404(Region, pk=region_id)
    region_code = get_current_region_code() or request.session.get("active_region_code") or "DE"
    return get_object_or_404(Region, code=region_code)


def _row_for(domain: str, row_code: str, region: Region):
    model, label_attr = DOMAIN_MODEL_MAP[domain]
    row = get_object_or_404(model.objects.all(), code=row_code, region=region)
    return row, getattr(row, label_attr, "") or ""


def _source_initial_from_refs(source_refs):
    initial = []
    for index, ref in enumerate(source_refs or []):
        initial.append(
            {
                "section": ref.get("section") or "general",
                "label": ref.get("label") or "",
                "description": ref.get("description") or "",
                "url": ref.get("url") or "",
                "sort_order": index,
            }
        )
    return initial


@login_required
def ui_provenance_edit(request):
    if not user_can_edit_ui_provenance(request.user):
        raise PermissionDenied("Keine Berechtigung zum Bearbeiten der Quelleninformationen.")

    domain = (request.GET.get("domain") or request.POST.get("domain") or "").strip()
    row_code = (request.GET.get("row_code") or request.POST.get("row_code") or "").strip()
    if domain not in DOMAIN_MODEL_MAP or not row_code:
        raise PermissionDenied("Ungültige Zeilen-Zuordnung.")

    region = _active_region_for_request(request)
    row, row_label = _row_for(domain, row_code, region)
    override = UIProvenanceOverride.objects.filter(
        domain=domain,
        row_code=row_code,
        region=region,
    ).prefetch_related("sources").first()

    return_url = _safe_return_url(request)

    if request.method == "POST":
        form = UIProvenanceEditorForm(request.POST)
        source_formset = SourceFormSet(request.POST, prefix="sources")
        if form.is_valid() and source_formset.is_valid():
            override, _created = UIProvenanceOverride.objects.update_or_create(
                domain=domain,
                row_code=row_code,
                region=region,
                defaults={
                    "row_label": row_label,
                    "general_information": form.cleaned_data["general_information"].strip(),
                    "status_information": form.cleaned_data["status_information"].strip(),
                    "ziel_information": form.cleaned_data["ziel_information"].strip(),
                    "is_active": form.cleaned_data["is_active"],
                },
            )
            override.sources.all().delete()
            source_rows = []
            for source_form in source_formset:
                if source_form.cleaned_data.get("DELETE"):
                    continue
                label = (source_form.cleaned_data.get("label") or "").strip()
                description = (source_form.cleaned_data.get("description") or "").strip()
                url = (source_form.cleaned_data.get("url") or "").strip()
                if not (label or description or url):
                    continue
                source_rows.append(
                    UIProvenanceSource(
                        override=override,
                        section=source_form.cleaned_data.get("section") or "general",
                        label=label,
                        description=description,
                        url=url,
                        sort_order=source_form.cleaned_data.get("sort_order") or 0,
                    )
                )
            UIProvenanceSource.objects.bulk_create(source_rows)
            return redirect(return_url)
    else:
        if override:
            initial = {
                "general_information": override.general_information,
                "status_information": override.status_information,
                "ziel_information": override.ziel_information,
                "is_active": override.is_active,
            }
            source_initial = [
                {
                    "section": source.section,
                    "label": source.label,
                    "description": source.description,
                    "url": source.url,
                    "sort_order": source.sort_order,
                }
                for source in override.sources.all()
            ]
        else:
            initial = split_notes_assumption_sections(getattr(row, "notes_assumption", ""))
            initial["is_active"] = True
            source_initial = _source_initial_from_refs(getattr(row, "source_refs", None))
        form = UIProvenanceEditorForm(initial=initial)
        source_formset = SourceFormSet(initial=source_initial, prefix="sources")

    return render(
        request,
        "simulator/ui_provenance_edit.html",
        {
            "form": form,
            "source_formset": source_formset,
            "domain": domain,
            "domain_label": dict(UIProvenanceOverride._meta.get_field("domain").choices).get(domain, domain),
            "row": row,
            "row_code": row_code,
            "row_label": row_label,
            "region": region,
            "return_url": return_url,
        },
    )
