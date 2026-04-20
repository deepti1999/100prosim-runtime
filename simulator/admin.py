from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from .models import (
    Formula,
    FormulaVariable,
    LandUse,
    RenewableData,
    VerbrauchData,
    WSData,
    WS365Formula,
    BalanceJob,
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
class LandUseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status_ha', 'target_ha', 'parent', 'quelle']
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
class RenewableDataAdmin(admin.ModelAdmin):
    # Show all entries with values only for fixed items
    list_display = ['code', 'name', 'category', 'subcategory', 'unit', 'status_display', 'target_display', 'is_fixed', 'user_editable', 'parent_code']
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
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make value fields readonly for calculated items, editable for fixed items"""
        if not obj:
            return ['formula']
        
        readonly = ['code', 'created_at', 'updated_at', 'formula']
        
        if not obj.is_fixed:
            readonly.extend(['status_value', 'target_value', 'user_input', 'user_editable'])
        
        return readonly
    

@admin.register(VerbrauchData)
class VerbrauchDataAdmin(admin.ModelAdmin):
    list_display = ['code', 'category_display', 'unit', 'status_display', 'ziel_display', 'user_percent_display', 'is_calculated', 'user_editable', 'data_type']
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
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make status/ziel readonly for calculated items"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_calculated:
            readonly.extend(['status', 'ziel', 'user_percent'])
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
        """Format number properly: commas for thousands (>=1000), decimals for smaller"""
        if value is None:
            return "-"
        
        # Always check if it's a whole number first
        if value == int(value):
            if value >= 1000:
                return f"{int(value):,}"  # Comma separator, no decimals for whole numbers
            else:
                return f"{int(value):,}"    # No decimals, comma for smaller whole numbers too
        else:
            # For non-whole numbers
            return f"{value:,.4f}".rstrip('0').rstrip('.')  # up to 4 decimals, comma thousands
    
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
