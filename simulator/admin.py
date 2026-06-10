from django.contrib import admin
from django import forms
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.http import urlencode
from .models import (
    AdminDataVersion,
    Formula,
    FormulaVariable,
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    UIProvenanceOverride,
    UIProvenanceSource,
    VerbrauchData,
    WSData,
    WS365Formula,
    BalanceJob,
)
from .admin_versioning import (
    capture_admin_version_payload,
    payload_size_mb,
    restore_admin_version_payload,
)

class DataTypeFilter(SimpleListFilter):
    title = 'Data Type'
    parameter_name = 'data_type'
    
    def lookups(self, request, model_admin):
        return (
            ('klik', 'KLIK'),
            ('gebaeudewaerme', 'Gebäudewärme'),
            ('prozesswaerme', 'Prozesswärme'),
            ('mobile_anwendungen', 'Mobile Anwendungen'),
            ('strom_endverbrauch', 'Strom-Endverbrauch'),
            ('endenergieverbrauch', 'Endenergieverbrauch'),
            ('other', 'Other'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'klik':
            return queryset.filter(code__startswith='1')
        elif self.value() == 'gebaeudewaerme':
            return queryset.filter(code__startswith='2')
        elif self.value() == 'prozesswaerme':
            return queryset.filter(code__startswith='3')
        elif self.value() == 'mobile_anwendungen':
            return queryset.filter(code__startswith='4')
        elif self.value() == 'strom_endverbrauch':
            return queryset.filter(code='5')
        elif self.value() == 'endenergieverbrauch':
            return queryset.filter(code='6')
        elif self.value() == 'other':
            return queryset.exclude(code__regex=r'^[1-6]')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "display_name",
        "active",
        "status_year",
        "target_year",
        "locale_code",
        "total_area_ha",
    ]
    list_filter = ["active", "target_year", "status_year"]
    search_fields = ["code", "display_name", "goal_description", "data_source_label"]
    ordering = ["code"]
    fieldsets = (
        ("Land / Region", {
            "fields": ("code", "display_name", "active", "locale_code"),
            "description": (
                "Hier werden Länder oder Regionen verwaltet. Neue Länder können "
                "sichtbar gemacht werden, ohne das Seitenlayout zu ändern."
            ),
        }),
        ("Planungsrahmen", {
            "fields": ("status_year", "target_year", "goal_description", "total_area_ha"),
            "description": (
                "Diese Werte steuern Beschriftungen wie Status-Jahr, Ziel-Jahr "
                "und Hauptziel in der Weboberfläche. Sie ändern keine Formeln."
            ),
        }),
        ("Datenquellen / Import", {
            "fields": ("data_source_label", "datenmodell_excel_hash"),
            "description": (
                "Technische Orientierung für importierte Daten und Anzeige im "
                "Jahresstrom-Diagramm."
            ),
        }),
        ("Jahresstrom-Konstanten", {
            "fields": ("installed_pmax_ely_gw", "installed_pmax_rv_gw"),
            "description": (
                "Regionsspezifische Diagrammwerte. Nur ändern, wenn die "
                "Datenbasis für diese Region geprüft wurde."
            ),
        }),
    )


class UIProvenanceOverrideAdminForm(forms.ModelForm):
    class Meta:
        model = UIProvenanceOverride
        fields = "__all__"
        labels = {
            "domain": "Bereich",
            "row_code": "Zeilen-Code",
            "row_label": "Zeilenname",
            "region": "Region",
            "is_active": "Aktiv anzeigen",
            "general_information": "Zusätzliche Information für Nutzer",
            "status_information": "Status-Erklärung",
            "ziel_information": "Ziel-Erklärung",
        }
        help_texts = {
            "domain": "Auf welcher Seite diese Zusatzinformation erscheinen soll.",
            "row_code": "Zum Beispiel LU_1.1, 9.4.1 oder 2.9.2.",
            "row_label": "Nur zur leichteren Orientierung im Admin.",
            "general_information": "Optionaler Einleitungstext, der oberhalb von Status/Ziel erscheint.",
            "status_information": "Kurze, klare Erklärung für den Status-Wert.",
            "ziel_information": "Kurze, klare Erklärung für den Ziel-Wert.",
            "is_active": "Nur aktive Einträge überschreiben die importierten Excel-Informationen.",
        }


class UIProvenanceSourceInlineForm(forms.ModelForm):
    class Meta:
        model = UIProvenanceSource
        fields = "__all__"
        labels = {
            "section": "Bereich",
            "label": "Kurztitel",
            "description": "Quellenbeschreibung",
            "url": "Link",
            "sort_order": "Reihenfolge",
        }
        help_texts = {
            "section": "Ob die Quelle zu Status, Ziel oder allgemein gehört.",
            "label": "Kurzer Titel wie GENESIS, DESTATIS oder Solarthermie Kollektorfläche.",
            "description": "Vollständige Beschreibung, die Nutzer im Popover sehen.",
            "url": "Externer Link, der bei 'Quelle öffnen' verwendet wird.",
            "sort_order": "Kleinere Zahlen erscheinen zuerst.",
        }


class UIProvenanceSourceInline(admin.TabularInline):
    model = UIProvenanceSource
    form = UIProvenanceSourceInlineForm
    extra = 1
    fields = ("section", "label", "description", "url", "sort_order")


@admin.register(AdminDataVersion)
class AdminDataVersionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "region",
        "status",
        "is_protected",
        "created_by",
        "captured_at",
        "payload_size",
        "payload_counts",
        "restore_button",
        "refresh_button",
    ]
    list_filter = ["region", "status", "is_protected", "created_by"]
    search_fields = ["name", "note"]
    ordering = ["-captured_at", "-updated_at"]
    list_per_page = 50
    readonly_fields = [
        "created_by",
        "captured_at",
        "created_at",
        "updated_at",
        "payload_summary",
        "payload",
    ]
    actions = ["restore_selected_version", "refresh_selected_versions"]

    fieldsets = (
        ("Admin-Szenario", {
            "fields": ("name", "region", "status", "is_protected", "note"),
            "description": (
                "Speichert den aktuellen globalen Admin-Datenstand als Admin-Szenario. "
                "Das ändert keine Formeln oder Werte direkt, sondern legt einen "
                "Wiederherstellungspunkt an."
            ),
        }),
        ("Gespeicherter Stand", {
            "fields": ("payload_summary", "captured_at", "created_by"),
            "description": (
                "Beim ersten Speichern wird automatisch der aktuelle Datenstand "
                "dieser Region erfasst. Über die Aktion 'ausgewähltes Szenario "
                "wiederherstellen' kann dieser Stand zurückgespielt werden."
            ),
        }),
        ("Technische Daten", {
            "fields": ("payload", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/restore/",
                self.admin_site.admin_view(self.restore_version_view),
                name="simulator_admindataversion_restore",
            ),
            path(
                "<int:object_id>/refresh/",
                self.admin_site.admin_view(self.refresh_version_view),
                name="simulator_admindataversion_refresh",
            ),
        ]
        return custom_urls + urls

    def has_restore_permission(self, request):
        return request.user.has_perm("simulator.restore_admin_data_version")

    def has_refresh_permission(self, request):
        return request.user.has_perm("simulator.refresh_admin_data_version")

    def has_protect_permission(self, request):
        return request.user.has_perm("simulator.protect_admin_data_version")

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not self.has_restore_permission(request):
            actions.pop("restore_selected_version", None)
        if not self.has_refresh_permission(request):
            actions.pop("refresh_selected_versions", None)
        return actions

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not self.has_protect_permission(request) and "is_protected" not in readonly:
            readonly.append("is_protected")
        return readonly

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        if not obj.payload:
            obj.payload = capture_admin_version_payload(obj.region.code)
            from django.utils import timezone

            obj.captured_at = timezone.now()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if obj.is_protected:
            self.message_user(
                request,
                "Dieses Admin-Szenario ist geschützt und wurde nicht gelöscht.",
                level=messages.ERROR,
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        protected = queryset.filter(is_protected=True).count()
        queryset = queryset.filter(is_protected=False)
        count = queryset.count()
        if count:
            super().delete_queryset(request, queryset)
        if protected:
            self.message_user(
                request,
                f"{protected} geschützte Admin-Szenario(s) wurden nicht gelöscht.",
                level=messages.WARNING,
            )

    def payload_size(self, obj):
        return f"{payload_size_mb(obj.payload)} MB"
    payload_size.short_description = "Größe"

    def payload_counts(self, obj):
        counts = (obj.payload or {}).get("counts") or {}
        if not counts:
            return "-"
        important = ["landuse", "renewable", "verbrauch", "formulas", "ui_provenance"]
        return ", ".join(f"{key}: {counts.get(key, 0)}" for key in important)
    payload_counts.short_description = "Inhalt"

    def payload_summary(self, obj):
        if not obj or not obj.payload:
            return "Noch kein Datenstand gespeichert. Beim Speichern wird automatisch ein Snapshot erzeugt."
        counts = (obj.payload or {}).get("counts") or {}
        lines = [
            f"Region: {(obj.payload or {}).get('region_code', '-')}",
            f"Größe: {payload_size_mb(obj.payload)} MB",
        ]
        for key in sorted(counts):
            lines.append(f"{key}: {counts[key]}")
        return format_html("<br>".join(lines))
    payload_summary.short_description = "Zusammenfassung"

    def restore_button(self, obj):
        url = reverse("admin:simulator_admindataversion_restore", args=[obj.pk])
        return format_html(
            '<a class="button" style="white-space:nowrap;" href="{}">Wiederherstellen</a>',
            url,
        )
    restore_button.short_description = "Wiederherstellen"

    def refresh_button(self, obj):
        if obj.is_protected:
            return format_html('<span style="color:#777;">geschützt</span>')
        url = reverse("admin:simulator_admindataversion_refresh", args=[obj.pk])
        return format_html(
            '<a class="button" style="white-space:nowrap;" href="{}">Mit aktuellem Stand überschreiben</a>',
            url,
        )
    refresh_button.short_description = "Aktueller Stand"

    def restore_version_view(self, request, object_id):
        if not self.has_restore_permission(request):
            self.message_user(
                request,
                "Sie haben keine Berechtigung, Admin-Szenarien wiederherzustellen.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        version = self.get_object(request, object_id)
        if version is None:
            self.message_user(request, "Admin-Szenario nicht gefunden.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        if request.method == "POST":
            restored = restore_admin_version_payload(version.payload)
            details = ", ".join(f"{key}: {value}" for key, value in restored.items())
            self.message_user(
                request,
                f'Admin-Szenario "{version.name}" wurde wiederhergestellt. {details}',
                level=messages.SUCCESS,
            )
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Admin-Szenario wiederherstellen",
            "version": version,
            "payload_counts": (version.payload or {}).get("counts") or {},
            "payload_size": payload_size_mb(version.payload),
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/simulator/admindataversion/confirm_restore.html",
            context,
        )

    def refresh_version_view(self, request, object_id):
        if not self.has_refresh_permission(request):
            self.message_user(
                request,
                "Sie haben keine Berechtigung, Admin-Szenarien neu zu speichern.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        version = self.get_object(request, object_id)
        if version is None:
            self.message_user(request, "Admin-Szenario nicht gefunden.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))
        if version.is_protected:
            self.message_user(
                request,
                "Geschützte Admin-Szenarien können nicht überschrieben werden.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        if request.method == "POST":
            from django.utils import timezone

            version.payload = capture_admin_version_payload(version.region.code)
            version.captured_at = timezone.now()
            version.save(update_fields=["payload", "captured_at", "updated_at"])
            self.message_user(
                request,
                f'Admin-Szenario "{version.name}" wurde mit dem aktuellen Admin-Datenstand neu gespeichert.',
                level=messages.SUCCESS,
            )
            return HttpResponseRedirect(reverse("admin:simulator_admindataversion_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Admin-Szenario überschreiben",
            "version": version,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/simulator/admindataversion/confirm_refresh.html",
            context,
        )

    def restore_selected_version(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Bitte genau ein Admin-Szenario auswählen, das wiederhergestellt werden soll.",
                level=messages.ERROR,
            )
            return
        version = queryset.first()
        restored = restore_admin_version_payload(version.payload)
        details = ", ".join(f"{key}: {value}" for key, value in restored.items())
        self.message_user(
            request,
            f'Admin-Szenario "{version.name}" wurde wiederhergestellt. {details}',
            level=messages.SUCCESS,
        )
    restore_selected_version.short_description = "Ausgewähltes Admin-Szenario wiederherstellen"

    def refresh_selected_versions(self, request, queryset):
        refreshed = 0
        skipped = 0
        from django.utils import timezone

        for version in queryset:
            if version.is_protected:
                skipped += 1
                continue
            version.payload = capture_admin_version_payload(version.region.code)
            version.captured_at = timezone.now()
            version.save(update_fields=["payload", "captured_at", "updated_at"])
            refreshed += 1
        self.message_user(
            request,
            f"{refreshed} Admin-Szenario(s) neu gespeichert. {skipped} geschützte Admin-Szenario(s) übersprungen.",
            level=messages.SUCCESS if refreshed else messages.WARNING,
        )
    refresh_selected_versions.short_description = "Ausgewählte Admin-Szenarien mit aktuellem Stand überschreiben"


@admin.register(UIProvenanceOverride)
class UIProvenanceOverrideAdmin(admin.ModelAdmin):
    form = UIProvenanceOverrideAdminForm
    list_display = [
        "domain",
        "row_code",
        "row_label",
        "region",
        "is_active",
        "updated_at",
    ]
    list_filter = ["domain", "region", "is_active"]
    search_fields = ["row_code", "row_label", "general_information", "status_information", "ziel_information"]
    ordering = ["domain", "row_code"]
    list_per_page = 50
    inlines = [UIProvenanceSourceInline]
    fieldsets = (
        ("Zeilen-Zuordnung", {
            "fields": ("domain", "row_code", "row_label", "region", "is_active"),
            "description": (
                "Diese Angaben sind nur für die Nutzeransicht gedacht. "
                "Sie ändern keine Formeln, Werte, Worker-Jobs oder Berechnungen."
            ),
        }),
        ("Informationstext", {
            "fields": ("general_information", "status_information", "ziel_information"),
            "description": (
                "Hier kann die benutzerfreundliche Erklärung gepflegt werden. "
                "Status und Ziel erscheinen im Popover getrennt."
            ),
        }),
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        for key in ("domain", "row_code", "row_label", "region"):
            value = request.GET.get(key)
            if value:
                initial[key] = value
        return initial


class UIProvenanceLinkMixin:
    ui_provenance_domain = None

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if "ui_provenance_link" not in base:
            base.append("ui_provenance_link")
        return base

    def ui_provenance_link(self, obj):
        if not obj or not self.ui_provenance_domain or not getattr(obj, "code", None) or not getattr(obj, "region_id", None):
            return "-"
        existing = UIProvenanceOverride.objects.filter(
            domain=self.ui_provenance_domain,
            row_code=obj.code,
            region_id=obj.region_id,
        ).first()
        if existing:
            url = reverse("admin:simulator_uiprovenanceoverride_change", args=[existing.pk])
            label = "UI-Info bearbeiten"
        else:
            params = urlencode(
                {
                    "domain": self.ui_provenance_domain,
                    "row_code": obj.code,
                    "row_label": getattr(obj, "name", None) or getattr(obj, "category", None) or "",
                    "region": obj.region_id,
                }
            )
            url = f"{reverse('admin:simulator_uiprovenanceoverride_add')}?{params}"
            label = "UI-Info anlegen"
        return format_html('<a href="{}">{}</a>', url, label)

    ui_provenance_link.short_description = "UI-Info"

class FormulaVariableInline(admin.TabularInline):
    model = FormulaVariable
    extra = 1
    fields = ("variable_name", "source_type", "source_key", "default_value", "is_required", "notes")
    classes = ['collapse']

@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("status_icon", "key", "formula_type_badge", "ws_row_type_badge", "category", "expression_short", "is_active", "version", "validation_badge", "updated_at")
    list_filter = ("category", "formula_type", "ws_row_type", "is_active", "validation_status", "is_fixed")
    search_fields = ("key", "expression", "description", "notes")
    inlines = [FormulaVariableInline]
    ordering = ("category", "key",)
    list_per_page = 50
    
    # Make fields editable in list view
    list_editable = ("is_active",)
    
    # Action buttons - INCLUDING CACHE CLEARING!
    actions = ['activate_formulas', 'deactivate_formulas', 'validate_formulas', 'export_formulas', 'clear_cache_action', 'clear_all_cache_action']
    
    fieldsets = (
        ('Formula Identification', {
            'fields': ('key', 'category', 'formula_type', 'is_fixed'),
            'description': 'Key will be auto-suffixed based on formula type: Status = no suffix, Ziel = _ziel or _target'
        }),
        (' WS Row Type (Energy Storage Only)', {
            'fields': ('ws_row_type',),
            'description': ' FOR WS FORMULAS ONLY: Select which rows this formula applies to:\n'
                          '• Day 1 Only - First day (no day_prev available)\n'
                          '• Days 2-365 - Pattern formula using day_prev.column\n'
                          '• Annual Summary - Legacy aggregate slot\n'
                          '• Legacy Reference - Legacy compatibility slot'
        }),
        ('Formula Expression', {
            'fields': ('expression', 'description'),
            'description': 'Use references like:\n'
                          '• Verbrauch: V_2_9_2_ziel, V_2_4_status\n'
                          '• Renewable: Renewable_1_1_2_1_2, Renewable_9_4_3\n'
                          '• WS sums: sums["sum_stromverbr"]\n'
                          '• WS pattern: day_prev.column, row.column'
        }),
        ('Status & Validation', {
            'fields': ('is_active', 'validation_status', 'validation_message', 'last_validated'),
            'classes': ('collapse',)
        }),
        ('Version & Notes', {
            'fields': ('version', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_validated')
    
    def status_icon(self, obj):
        """Show active/inactive icon"""
        if obj.is_active:
            return format_html('<span style="color: {}; font-size: 16px;">●</span>', 'green')
        return format_html('<span style="color: {}; font-size: 16px;">○</span>', 'red')
    status_icon.short_description = ''
    
    def formula_type_badge(self, obj):
        """Show formula type as colored badge"""
        if obj.formula_type == 'ziel':
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                '#0066cc',
                'ZIEL'
            )
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            '#666',
            'STATUS'
        )
    formula_type_badge.short_description = 'Type'
    
    def ws_row_type_badge(self, obj):
        """Show WS row type as colored badge (only for WS category)"""
        if obj.category != 'ws' or not obj.ws_row_type or obj.ws_row_type == 'all':
            return ''
        
        colors = {
            'day_1': '#28a745',        # Green
            'days_2_365': '#007bff',   # Blue
            'annual_summary': '#fd7e14',      # Orange
            'legacy_reference': '#6c757d',    # Gray
            'row_368': '#17a2b8',      # Cyan
        }
        labels = {
            'day_1': 'Day 1',
            'days_2_365': '2-365',
            'annual_summary': 'Annual',
            'legacy_reference': 'Legacy Ref',
            'row_368': '368+',
        }
        color = colors.get(obj.ws_row_type, '#999')
        label = labels.get(obj.ws_row_type, 'Legacy')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            label
        )
    ws_row_type_badge.short_description = 'WS Row'
    
    def expression_short(self, obj):
        """Show shortened expression"""
        expr = obj.expression or ''
        if len(expr) > 60:
            return format_html('<span title="{}">{}</span>', expr, expr[:60] + '...')
        return format_html('{}', expr) if expr else ''
    expression_short.short_description = 'Expression'
    
    def validation_badge(self, obj):
        """Show validation status as colored badge"""
        colors = {
            'valid': 'green',
            'invalid': 'red',
            'pending': 'orange',
            'warning': 'darkorange',
        }
        status = obj.validation_status or 'pending'
        color = colors.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            status.upper()
        )
    validation_badge.short_description = 'Status'
    
    # Admin actions
    def activate_formulas(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} formula(s) activated.')
    activate_formulas.short_description = " Activate selected formulas"
    
    def deactivate_formulas(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} formula(s) deactivated.')
    deactivate_formulas.short_description = " Deactivate selected formulas"
    
    def validate_formulas(self, request, queryset):
        """Validate selected formulas using comprehensive validator"""
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        
        for formula in queryset:
            is_valid = formula.validate_expression()
            
            if formula.validation_status == 'valid':
                valid_count += 1
            elif formula.validation_status == 'warning':
                warning_count += 1
            else:
                invalid_count += 1
        
        total = queryset.count()
        self.message_user(
            request, 
            f'Validated {total} formulas:  {valid_count} valid,  {warning_count} warnings,  {invalid_count} invalid'
        )
    validate_formulas.short_description = " Validate selected formulas"
    
    def export_formulas(self, request, queryset):
        """Export selected formulas as JSON"""
        import json
        from django.http import HttpResponse
        
        formulas = []
        for formula in queryset:
            formulas.append({
                'key': formula.key,
                'expression': formula.expression,
                'description': formula.description,
                'category': formula.category,
                'formula_type': formula.formula_type,
                'is_fixed': formula.is_fixed,
                'is_active': formula.is_active,
            })
        
        response = HttpResponse(json.dumps(formulas, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="formulas.json"'
        return response
    export_formulas.short_description = " Export selected formulas as JSON"
    
    def clear_cache_action(self, request, queryset):
        """Clear cache for selected formulas - ensures changes are immediately visible"""
        from django.core.cache import cache
        from simulator.formula_service import FormulaService
        
        count = 0
        for formula in queryset:
            # Clear Django cache
            cache.delete(f'formula_{formula.key}')
            # Clear FormulaService cache
            service = FormulaService()
            service.clear_cache(formula.key)
            count += 1
        
        self.message_user(request, f"Cache cleared for {count} formula(s) - changes will be visible immediately!")
    clear_cache_action.short_description = " Clear cache for selected formulas"
    
    def clear_all_cache_action(self, request, queryset):
        """Clear ALL formula caches - nuclear option for when formulas aren't updating"""
        from django.core.cache import cache
        from simulator.formula_service import FormulaService
        
        # Clear all Django cache
        cache.clear()
        
        # Clear FormulaService cache
        service = FormulaService()
        service.clear_cache()
        
        self.message_user(request, "ALL formula caches cleared! All formula changes are now active.")
    clear_all_cache_action.short_description = " Clear ALL formula caches"
    
    def save_model(self, request, obj, form, change):
        """Override to show cache clearing message - WS recalculation is handled by signals"""
        super().save_model(request, obj, form, change)
        if change:
            self.message_user(request, f"Formula {obj.key} updated - dependent values will auto-recalculate!")
        else:
            self.message_user(request, f"Formula {obj.key} created - dependent values will auto-recalculate!")
        
    
    def delete_model(self, request, obj):
        """Override to show cache clearing message"""
        key = obj.key
        category = obj.category
        super().delete_model(request, obj)
        self.message_user(request, f"Formula {key} deleted - dependent values will auto-recalculate!")

@admin.register(LandUse)
class LandUseAdmin(UIProvenanceLinkMixin, admin.ModelAdmin):
    ui_provenance_domain = "landuse"
    list_display = ['code', 'name', 'status_ha', 'target_ha', 'parent', 'quelle', 'ui_provenance_link']
    list_filter = ['quelle', 'parent']
    search_fields = ['code', 'name']
    ordering = ['code']
    
    list_per_page = 25
    
    # Add action to manually trigger cascade updates
    actions = ['trigger_cascade_update', 'force_save_selected']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'parent', 'quelle')
        }),
        ('Data (Editable)', {
            'fields': ('status_ha', 'target_ha', 'user_percent', 'target_locked'),
            'description': 'IMPORTANT: After changing status_ha or target_ha, click SAVE to trigger cascade updates to dependent Renewable records.'
        }),
        ('UI-Zusatzinformation', {
            'fields': ('ui_provenance_link',),
            'description': 'Benutzerfreundliche Information + Quellen für die Popover. UI-only, ohne Einfluss auf Berechnung oder Formeln.'
        }),
        ('Formulas (Optional)', {
            'fields': ('status_formula_key', 'target_formula_key'),
            'description': 'Provide formula keys to calculate values from DB-driven formulas instead of hardcoding.',
            'classes': ('collapse',)
        }),
    )
    
    def trigger_cascade_update(self, request, queryset):
        """Manually trigger cascade update for selected LandUse records"""
        updated_count = 0
        for landuse in queryset:
            # Force recalculation by calling the cascade method
            landuse._recalculate_renewable_dependents()
            updated_count += 1
        
        self.message_user(
            request,
            f'Triggered cascade update for {updated_count} LandUse record(s). '
            f'Dependent Renewable records have been recalculated.',
            level='SUCCESS'
        )
    trigger_cascade_update.short_description = " Trigger cascade update to Renewable data"
    
    def force_save_selected(self, request, queryset):
        """Force save selected records to ensure database persistence"""
        count = 0
        for landuse in queryset:
            landuse.save()
            count += 1
        
        self.message_user(
            request,
            f'Force-saved {count} LandUse record(s) to database.',
            level='SUCCESS'
        )
    force_save_selected.short_description = "Force save selected records"
    
    def save_model(self, request, obj, form, change):
        """Save and allow cascade so dependent renewables update automatically."""
        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            f'Saved {obj.code}: status_ha={obj.status_ha}, target_ha={obj.target_ha}',
            level='SUCCESS'
        )

@admin.register(RenewableData)
class RenewableDataAdmin(UIProvenanceLinkMixin, admin.ModelAdmin):
    ui_provenance_domain = "renewable"
    # Show all entries with values only for fixed items
    list_display = ['code', 'name', 'category', 'subcategory', 'unit', 'status_display', 'target_display', 'is_fixed', 'user_editable', 'parent_code', 'ui_provenance_link']
    list_filter = ['category', 'subcategory', 'is_fixed', 'user_editable', 'created_at']
    search_fields = ['code', 'name', 'category', 'subcategory']
    ordering = ['code']
    
    list_editable = ['is_fixed', 'user_editable']
    list_per_page = 100  # Show more entries per page
    
    # Add JavaScript for instant field toggling
    class Media:
        js = ('admin/js/renewable_toggle.js',)
    
    def status_display(self, obj):
        """Show status value only for fixed items (non-formula items)"""
        if obj.is_fixed:
            return obj.status_value if obj.status_value is not None else "-"
        return ""  # Empty for calculated items
    status_display.short_description = 'Status Value'
    
    def target_display(self, obj):
        """Show target value only for fixed items (non-formula items)"""
        if obj.is_fixed:
            return obj.target_value if obj.target_value is not None else "-"
        return ""  # Empty for calculated items
    target_display.short_description = 'Target Value'
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'category', 'subcategory', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent_code',),
            'description': 'Hierarchical parent relationship.'
        }),
        ('Data Values - Editable for Fixed Items Only', {
            'fields': ('unit', 'status_value', 'target_value', 'user_input'),
            'description': 'Edit values for fixed items. Formula items are calculated automatically.'
        }),
        ('User Frontend Control', {
            'fields': ('user_editable',),
            'description': 'Enable this to allow frontend users to edit this row input. Saving user input updates target value.'
        }),
        ('Calculation', {
            'fields': ('is_fixed', 'formula'),
            'description': 'Whether value is fixed or calculated, and formula if applicable.'
        }),
        ('Metadata', {
            'fields': ('source', 'notes'),
            'classes': ('collapse',)
        }),
        ('UI-Zusatzinformation', {
            'fields': ('ui_provenance_link',),
            'description': 'Benutzerfreundliche Information + Quellen für die Popover. UI-only, ohne Einfluss auf Berechnung oder Formeln.'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make value fields readonly for calculated items, editable for fixed items"""
        if not obj:
            readonly = list(super().get_readonly_fields(request, obj))
            if 'formula' not in readonly:
                readonly.append('formula')
            return readonly
        
        readonly = list(super().get_readonly_fields(request, obj))
        for field in ['code', 'created_at', 'updated_at', 'formula']:
            if field not in readonly:
                readonly.append(field)
        
        if not obj.is_fixed:
            for field in ['status_value', 'target_value', 'user_input', 'user_editable']:
                if field not in readonly:
                    readonly.append(field)
        
        return readonly
    

@admin.register(VerbrauchData)
class VerbrauchDataAdmin(UIProvenanceLinkMixin, admin.ModelAdmin):
    ui_provenance_domain = "verbrauch"
    list_display = ['code', 'category_display', 'unit', 'status_display', 'ziel_display', 'user_percent_display', 'is_calculated', 'user_editable', 'data_type', 'ui_provenance_link']
    list_filter = [DataTypeFilter, 'is_calculated', 'user_editable', 'unit', 'created_at']
    search_fields = ['code', 'category']
    ordering = ['code']
    
    list_editable = ['is_calculated', 'user_editable']
    list_per_page = 30
    
    fieldsets = (
        ('Identification', {
            'fields': ('code', 'category')
        }),
        ('Data Values', {
            'fields': ('unit', 'status', 'ziel', 'user_percent'),
            'description': 'Current status, target (Ziel), and user percentage values. Only editable for fixed values.'
        }),
        ('User Frontend Control', {
            'fields': ('user_editable',),
            'description': 'Check this box to allow users to edit this field in the frontend. Users will be able to modify the value and trigger recalculations.'
        }),
        ('Calculation', {
            'fields': ('is_calculated',),
            'description': 'Whether this value should be calculated via formula. Formulas are managed in the Formula admin page.'
        }),
        ('UI-Zusatzinformation', {
            'fields': ('ui_provenance_link',),
            'description': 'Benutzerfreundliche Information + Quellen für die Popover. UI-only, ohne Einfluss auf Berechnung oder Formeln.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make status/ziel readonly for calculated items"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_calculated:
            for field in ['status', 'ziel', 'user_percent']:
                if field not in readonly:
                    readonly.append(field)
        return readonly
    
    readonly_fields = ['created_at', 'updated_at']
    
    def category_display(self, obj):
        """Truncate long category names for better display and add CSS classes"""
        category_text = obj.category
        if len(category_text) > 50:
            category_text = category_text[:47] + "..."
        
        # Add bold styling for "Strom-Endverbrauch insgesamt"
        if "Strom-Endverbrauch insgesamt" in obj.category:
            return format_html('<span style="font-weight: bold;">{}</span>', category_text)
        
        # Add bold styling for "Endenergieverbrauch insgesamt"
        if "Endenergieverbrauch insgesamt" in obj.category:
            return format_html('<span style="font-weight: bold;">{}</span>', category_text)
        
        # Add green styling for FC-Traktion alternative entries
        if "Alternativ zur" in obj.category and "Brennstoffzellen (FC)" in obj.category:
            return format_html('<span style="color: green; font-style: italic;">{}</span>', category_text)
        
        return category_text
    category_display.short_description = 'Category'
    
    def format_number(self, value):
        """Format number using German convention (per stakeholder PDF §2.5.2):
        dot as thousand separator, comma as decimal separator.
        """
        if value is None:
            return "-"

        def _de(s):
            # Build with English thousand-comma / decimal-dot first, then swap
            # using a temporary placeholder so we don't double-replace.
            return s.replace(",", "⁣").replace(".", ",").replace("⁣", ".")

        # Whole number?
        if value == int(value):
            return _de(f"{int(value):,}")
        # Non-whole: up to 4 decimals, no trailing zeros.
        return _de(f"{value:,.4f}".rstrip("0").rstrip("."))
    
    def status_display(self, obj):
        """Format status value for display - only show for fixed values"""
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        if obj.code.startswith('4.3.'):
            return ""
        
        if obj.code in fixed_items or not obj.is_calculated:
            if obj.code == '2.4.5':
                result = self.format_number(obj.status)
                return f"{result}" if result == "0" else result
            # Only show if value exists
            if obj.status is not None:
                return self.format_number(obj.status)
        return ""  # Empty for calculated items or items without values
    status_display.short_description = 'Status'
    
    def ziel_display(self, obj):
        """Format ziel value for display - only show for fixed values"""
        if "Alternativ zur" in obj.category and "Brennstoffzellen (FC)" in obj.category:
            return "(Passiv)"
        
        if obj.code.startswith('4.3.'):
            return ""
        
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        if obj.code in fixed_items or not obj.is_calculated:
            # Only show if value exists
            if obj.ziel is not None:
                return self.format_number(obj.ziel)
        return ""  # Empty for calculated items or items without values
    ziel_display.short_description = 'Ziel'
    
    def user_percent_display(self, obj):
        """Format user_percent value for display - only show for fixed values"""
        if obj.code.startswith('4.3.'):
            return ""
        
        # Special list of fixed items that should show values
        fixed_items = ['4.2.1', '4.2.2', '4.2.4']
        
        if obj.code in fixed_items or not obj.is_calculated:
            if obj.user_percent is not None:
                return self.format_number(obj.user_percent)
        return ""  # Empty for calculated items or items without values
    user_percent_display.short_description = 'User %'

    def save_model(self, request, obj, form, change):
        """Save the verbrauch data entry."""
        super().save_model(request, obj, form, change)
    
    def data_type(self, obj):
        """Show whether this is KLIK, Gebäudewärme, Prozesswärme, Mobile Anwendungen, Strom-Endverbrauch, or Endenergieverbrauch data"""
        if obj.code.startswith('1'):
            return "KLIK"
        elif obj.code.startswith('2'):
            return "Gebäudewärme"
        elif obj.code.startswith('3'):
            return "Prozesswärme"
        elif obj.code.startswith('4'):
            return "Mobile Anwendungen"
        elif obj.code == '5':
            return "Strom-Endverbrauch"
        elif obj.code == '6':
            return "Endenergieverbrauch"
        else:
            return "Other"
    data_type.short_description = 'Type'


@admin.register(GebaeudewaermeData)
class GebaeudewaermeDataAdmin(UIProvenanceLinkMixin, admin.ModelAdmin):
    ui_provenance_domain = "gebaeudewaerme"
    list_display = ["code", "category", "unit", "status", "ziel", "is_calculated", "ui_provenance_link"]
    list_filter = ["is_calculated", "unit", "created_at"]
    search_fields = ["code", "category"]
    ordering = ["code"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Identification", {
            "fields": ("code", "category"),
        }),
        ("Data Values", {
            "fields": ("unit", "status", "ziel", "user_percent"),
        }),
        ("Calculation", {
            "fields": ("formula", "is_calculated", "status_calculated", "ziel_calculated"),
        }),
        ("UI-Zusatzinformation", {
            "fields": ("ui_provenance_link",),
            "description": "Benutzerfreundliche Information + Quellen für die Popover. UI-only, ohne Einfluss auf Berechnung oder Formeln.",
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

@admin.register(WSData)
class WSDataAdmin(admin.ModelAdmin):
    """Admin for WS daily inputs only (4 columns)."""

    list_display = [
        "tag_im_jahr",
        "solar_promille",
        "wind_promille",
        "heizung_abwaerm_promille",
        "verbrauch_promille",
        "owner",
        "updated_at",
    ]
    list_filter = ["owner"]
    search_fields = ["tag_im_jahr"]
    ordering = ["owner", "tag_im_jahr"]
    list_per_page = 100

    fieldsets = (
        ("Day", {"fields": ("tag_im_jahr", "owner")}),
        (
            "WS Input Columns",
            {
                "fields": (
                    "solar_promille",
                    "wind_promille",
                    "heizung_abwaerm_promille",
                    "verbrauch_promille",
                ),
                "description": "Only 4 WS input columns are stored. Derived WS values are calculated from WS 365 formulas (Admin: WS 365 Formulas).",
            },
        ),
    )

@admin.register(WS365Formula)
class WS365FormulaAdmin(admin.ModelAdmin):
    list_display = (
        "column_name",
        "stage",
        "order",
        "is_active",
        "expression_preview",
        "updated_at",
    )
    list_filter = ("stage", "is_active")
    search_fields = ("column_name", "expression", "day1_expression", "description")
    ordering = ("stage", "order", "column_name")
    list_editable = ("order", "is_active")
    list_per_page = 100

    fieldsets = (
        (
            "Formula Identity",
            {
                "fields": ("column_name", "stage", "order", "is_active", "description"),
                "description": "Use a short key (example: new_data). Spaces are auto-converted to underscores.",
            },
        ),
        (
            "Expressions",
            {
                "fields": ("expression", "day1_expression"),
                "description": (
                    "Helpers: IF(cond,true,false), MIN, MAX, ABS, ROUND, PREV('col'). "
                    "DB lookups: REN_TARGET('9.1.5'), REN_STATUS('9.1.5'), "
                    "VER_ZIEL('2.9.2'), VER_STATUS('2.9.2'), LU_TARGET('LU_2.1'), LU_STATUS('LU_2.1'). "
                    "For stage=post, COL_MIN('col'), COL_MAX('col'), COL_SUM('col') are available."
                ),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def expression_preview(self, obj):
        expr = (obj.expression or "").strip().replace("\n", " ")
        if len(expr) > 80:
            return f"{expr[:80]}..."
        return expr
    expression_preview.short_description = "Expression"

@admin.register(BalanceJob)
class BalanceJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job_type",
        "status",
        "attempts",
        "created_by",
        "created_at",
        "started_at",
        "finished_at",
    )
    list_filter = ("job_type", "status", "created_at")
    search_fields = ("id", "error", "created_by__username")
    readonly_fields = (
        "id",
        "job_type",
        "status",
        "payload",
        "result",
        "error",
        "attempts",
        "created_by",
        "created_at",
        "started_at",
        "finished_at",
        "updated_at",
    )
