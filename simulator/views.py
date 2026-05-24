from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
from .models import (
    BalanceJob, LandUse, VerbrauchData
)
from simulator.input_api import (
    _check_landuse_increase_limit,
    _get_landuse_current_percent,
    update_landuse_percent,
)
from simulator.recalc_service import unified_recalc_all
from simulator.ws_queue_api import _queue_or_reuse_balance_job

_SIMULATOR_VERBOSE_PRINTS = os.environ.get("SIMULATOR_VERBOSE_PRINTS", "false").lower() == "true"
if not _SIMULATOR_VERBOSE_PRINTS:
    def print(*args, **kwargs):  # type: ignore[override]
        return None

def update_user_percent(request):
    """API endpoint to save user percentage input for land use data"""
    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_percent = data.get('user_percent')
        
        if not code:
            return JsonResponse({'success': False, 'error': 'Code is required'})
            
        # Get the land use record (with parent for target calc)
        landuse = get_object_or_404(LandUse.objects.select_related('parent'), code=code)

        # Capture pre-edit value for history logging (Phase 6-A, T61).
        old_user_percent = landuse.user_percent

        # Update user_percent (allow None/empty for clearing)
        if user_percent == '' or user_percent is None:
            landuse.user_percent = None
        else:
            try:
                percent_val = float(user_percent)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid percentage value'})

            is_valid, details = _check_landuse_increase_limit(landuse, percent_val)
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': f"Cannot increase by more than {details['max_increase_points']:.0f} percentage points from baseline.\n\n"
                            f"Baseline (Status): {details['baseline_percent']:.2f}%\n"
                            f"Current Input: {details['current_percent']:.2f}%\n"
                            f"Requested: {details['requested_percent']:.2f}%\n"
                            f"Increase from baseline: {details['increase_from_baseline']:.2f} points\n"
                            f"Maximum allowed: {details['max_allowed_value']:.2f}%",
                    'current_value': float(details['current_percent']),
                    'baseline_value': float(details['baseline_percent']),
                    'max_allowed_value': float(details['max_allowed_value']),
                })

            if landuse.target_locked:
                landuse.target_locked = False

            # Recalculate target_ha from parent target (if available)
            parent_target = landuse.parent.target_ha if landuse.parent else None
            if parent_target is not None:
                landuse.target_ha = (parent_target * percent_val) / 100.0

            landuse.user_percent = percent_val

        landuse.save()

        # Phase 6-A (T61): log user-initiated modification.
        try:
            from .models import ModificationHistoryEntry
            ModificationHistoryEntry.objects.create(
                owner=request.user if request.user.is_authenticated else None,
                model_label="LandUse",
                code=code or "",
                field="user_percent",
                value_before=old_user_percent,
                value_after=landuse.user_percent,
                source="user",
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': f'Saved {code}: {landuse.user_percent}%',
            'code': code,
            'user_percent': landuse.user_percent,
            'target_ha': landuse.target_ha,
        })
        
    except LandUse.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Land use code {code} not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def save_all_user_inputs(request):
    """
    API endpoint to save all user input values at once.
    FIXED: Uses model save() to trigger signals for auto-cascade.
    Only the LAST save triggers the full cascade to avoid redundant recalcs.
    NOW TRACKS: old → new values for frontend display
    """
    try:
        data = json.loads(request.body)
        user_inputs = data.get('user_inputs', {}) or {}
        
        saved_count = 0
        skipped_locked = 0
        errors = []
        changes = []  # Track old → new values
        
        items_to_save = []
        non_empty_codes = [
            code for code, percent in user_inputs.items()
            if percent not in ('', None)
        ]
        landuse_by_code = {
            lu.code: lu
            for lu in LandUse.objects.select_related('parent').filter(code__in=non_empty_codes)
        }
        
        # First pass: prepare all updates
        for code, percent in user_inputs.items():
            try:
                if percent == '' or percent is None:
                    continue
                    
                percent_val = float(percent)
                
                landuse = landuse_by_code.get(code)
                if not landuse:
                    errors.append(f'Code {code} not found')
                    continue
                
                current_percent = _get_landuse_current_percent(landuse)

                if abs(percent_val - current_percent) < 1e-9:
                    continue

                is_valid, details = _check_landuse_increase_limit(landuse, percent_val)
                if not is_valid:
                    errors.append(
                        f"{code}: Cannot increase by {details['increase_from_baseline']:.2f} points "
                        f"from baseline {details['baseline_percent']:.2f}% "
                        f"(max +{details['max_increase_points']:.0f} -> {details['max_allowed_value']:.2f}%)."
                    )
                    continue  # Skip this item
                
                unlocked_target = False
                if landuse.target_locked:
                    landuse.target_locked = False
                    unlocked_target = True
                
                # Store old values for change tracking
                old_target_ha = landuse.target_ha
                old_user_percent = landuse.user_percent
                
                if landuse.parent and landuse.parent.target_ha:
                    new_target_ha = (landuse.parent.target_ha * percent_val) / 100.0
                else:
                    new_target_ha = landuse.target_ha  # Keep existing if no parent
                
                landuse.user_percent = percent_val
                landuse.target_ha = new_target_ha
                update_fields = ['user_percent', 'target_ha']
                if unlocked_target:
                    update_fields.append('target_locked')
                landuse._save_all_update_fields = update_fields
                
                # Track the change
                changes.append({
                    'code': code,
                    'name': landuse.name,
                    'old_percent': round(old_user_percent, 2) if old_user_percent else None,
                    'new_percent': round(percent_val, 2),
                    'old_ha': round(old_target_ha, 2) if old_target_ha else None,
                    'new_ha': round(new_target_ha, 2),
                    'change_ha': round(new_target_ha - old_target_ha, 2) if old_target_ha else None
                })
                
                items_to_save.append(landuse)
                saved_count += 1
                
            except (ValueError, TypeError):
                errors.append(f'Invalid value for {code}: {percent}')
            except Exception as e:
                errors.append(f'Error saving {code}: {str(e)}')
        
        if items_to_save:
            LandUse.objects.bulk_update(
                items_to_save,
                ['user_percent', 'target_ha', 'target_locked'],
                batch_size=500,
            )

        host = request.get_host() if hasattr(request, "get_host") else ""
        inline_recalc = settings.DEBUG or host.startswith("testserver")

        if inline_recalc and items_to_save:
            summary = unified_recalc_all()
            return JsonResponse({
                'success': True,
                'queued': False,
                'saved_count': saved_count,
                'skipped_locked': skipped_locked,
                'errors': errors,
                'changes': changes,
                'summary': summary,
                'message': f'Saved {saved_count} values and recalculated.'
                           + (f' with {len(errors)} errors' if errors else '')
            })

        job = None
        if items_to_save:
            job = _queue_or_reuse_balance_job(
                request.user,
                BalanceJob.TYPE_LANDUSE_RECALC,
                {'scope': 'landuse'},
            )

        return JsonResponse({
            'success': True,
            'queued': bool(job),
            'job_id': str(job.id) if job else None,
            'status': job.status if job else None,
            'saved_count': saved_count,
            'skipped_locked': skipped_locked,
            'errors': errors,
            'changes': changes,  # Include changes for frontend display
            'message': (
                f'Saved {saved_count} values'
                + (' and queued recalculation.' if job else '')
                + (f' with {len(errors)} errors' if errors else '')
            )
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def update_downwards(node, new_percent, total_area):
    """Recursive downward update: parent drives children proportionally"""
    node.user_percent = new_percent
    node.user_ha = total_area * (new_percent / 100)
    node.save()
    
    print(f"Updated {node.code}: {new_percent}% = {node.user_ha:.2f}ha")

    children = node.children.all()
    if not children:
        return

    total_target = sum(child.target_ha for child in children)
    for child in children:
        ratio = child.target_ha / total_target if total_target > 0 else 0
        child_percent = (node.user_ha * ratio / total_area) * 100
        print(f" Cascading to {child.code}: ratio={ratio:.3f}, new_percent={child_percent:.2f}%")
        update_downwards(child, child_percent, total_area)

def update_upwards(node, total_area):
    """Recursive upward update: children drive parent by summing"""
    parent = node.parent
    if not parent:
        return
    
    parent.user_ha = sum(c.user_ha for c in parent.children.all())
    parent.user_percent = (parent.user_ha / total_area) * 100
    parent.save()
    
    print(f"⬆ Updated parent {parent.code}: {parent.user_percent:.2f}% = {parent.user_ha:.2f}ha (sum of children)")

    update_upwards(parent, total_area)  # climb upwards

def update_node(node, new_percent, total_area):
    """Master function: determines update direction based on node type"""
    if node.children.exists():  # parent node changed
        update_downwards(node, new_percent, total_area)
    else:  # leaf node changed
        node.user_percent = new_percent
        node.user_ha = total_area * (new_percent / 100)
        node.save()
        update_upwards(node, total_area)

@csrf_exempt  
@require_http_methods(["POST"])
def update_user_percent_by_code(request, code):
    """API endpoint to update user_percent with proper hierarchical cascading.

    Renamed from update_user_percent to avoid shadowing the body-based
    update_user_percent(request) at the top of this file. Python keeps
    only the last `def` at module scope, so the earlier body-based view
    was silently replaced and the `/api/update-user-percent/` URL
    (which has no `code` path param) was 500'ing.
    """
    try:
        node = get_object_or_404(LandUse, code=code)
        new_percent = float(request.POST.get("user_percent", 0))
        
        # Get total area from root node
        root_node = LandUse.objects.get(code="0")
        total_area = root_node.status_ha
        
        print(f"\n{'='*50}")
        print(f" API CALL: Updating {code} = {new_percent}%")
        print(f" Total area: {total_area:.2f}ha")
        
        # Enforce absolute +3pp cap from baseline status share
        if node.parent:
            is_valid, details = _check_landuse_increase_limit(node, new_percent)
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': (
                        f"Cannot increase {code} above {details['max_allowed_value']:.2f}% "
                        f"(baseline {details['baseline_percent']:.2f}% + "
                        f"{details['max_increase_points']:.0f}pp limit)."
                    ),
                    'baseline_value': float(details['baseline_percent']),
                    'max_allowed_value': float(details['max_allowed_value']),
                })

        # Use master update function
        update_node(node, new_percent, total_area)
        
        # Determine message based on node type
        if node.children.exists():
            message = f"Updated parent {code} and cascaded downwards to {node.children.count()} children"
        else:
            message = f"Updated leaf {code} and cascaded upwards to parents"
            
        print(f"{message}")
        print(f"{'='*50}\n")
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'code': code,
            'user_percent': new_percent
        })
        
    except LandUse.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'LandUse with code {code} not found'})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid user_percent value'})
    except Exception as e:
        print(f"Error updating {code}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def verbrauch_view(request):
    """Energy Consumption Data (Verbrauch) - FRESH calculated values from database"""
    from .models import VerbrauchData, RenewableData, LandUse
    from django.db import connection
    from .ui_provenance_service import load_ui_provenance_override_map, payload_for_row
    
    # Force fresh database read (clear any Django query cache)
    connection.queries_log.clear() if hasattr(connection, 'queries_log') else None
    
    # Get all verbrauch data from database - force fresh query
    verbrauch_data = list(VerbrauchData.objects.all().order_by('code'))
    provenance_map = load_ui_provenance_override_map("verbrauch", verbrauch_data)
    
    # Convert to list of dictionaries with natural sorting
    temp_data = []
    for item in verbrauch_data:
        # Force refresh from database
        item.refresh_from_db()
        provenance = payload_for_row(item, "verbrauch", provenance_map)
        
        display_status = item.status
        display_ziel = item.ziel
        
        if "Alternativ zur" in item.category and "Brennstoffzellen (FC)" in item.category:
            from django.utils.safestring import mark_safe
            if item.user_percent == 100.0:
                display_ziel = mark_safe('<span style="color: blue; font-weight: bold;">Aktiv</span>')
            else:
                display_ziel = mark_safe('<span style="color: green; font-weight: bold;">(Passiv)</span>')
        
        show_user_percent = item.user_percent if not item.is_calculated else None
        
        # Calculated fields should never be user_editable
        is_user_editable = item.user_editable and not item.is_calculated
        
        temp_data.append({
            'code': item.code,
            'category': item.category,
            'unit': item.unit,
            'status': display_status,
            'ziel': display_ziel,
            'user_percent': show_user_percent,  # Empty for calculated fields
            'is_calculated': item.is_calculated,
            'user_editable': is_user_editable,  # Never editable if calculated
            # §2.3 Phase A provenance fields
            'source_url': provenance['source_url'],
            'notes_assumption': provenance['notes_assumption'],
            'source_refs': provenance['source_refs'],
            'origin': provenance['origin'],
            'provenance_override_active': provenance['provenance_override_active'],
        })
    
    # Apply natural sorting (same as renewable energy)
    def natural_sort_key(item):
        """Natural sorting for hierarchical codes like 1, 1.1, 1.1.1, 1.2, etc."""
        parts = item['code'].split('.')
        return [int(part) for part in parts]
    
    temp_data.sort(key=natural_sort_key)
    
    category_headings = {
        '1': 'Kraft, Licht, Information, Kommunikation, Kälte (KLIK)',
        '2': 'Gebäudewärme (GW)',
        '3': 'Prozesswärme (PW)',
        '4': 'Mobile Anwendungen (MA)',
        '5': 'MA Luftverkehr',
        '6': 'Endenergieverbrauch MA gesamt',
        '9': 'Grundstoff-Synthetisierung',
        '10': 'Fossil',
    }
    
    # Track which category headings have been added
    added_categories = set()
    
    data = []
    
    for item in temp_data:
        code = item['code']
        
        major_category = code.split('.')[0]
        
        if major_category in category_headings and major_category not in added_categories:
            data.append({
                'is_section_header': False,
                'is_category_heading': True,
                'code': major_category,
                'category': category_headings[major_category],
                'unit': '',
                'status': None,
                'ziel': None,
                'user_percent': None,
                'is_calculated': False,
                'user_editable': False,
            })
            added_categories.add(major_category)
        
        if code in category_headings and '.' not in code:
            continue  # Skip - the heading already covers this
        
        # Mark as not a section header (no blue rows)
        item['is_section_header'] = False
        item['is_category_heading'] = False
        data.append(item)
    
    return render(request, 'simulator/verbrauch.html', {"data": data})

def gebaeudewaerme_view(request):
    """Building Heat Data (Gebäudewärme) - Load from database"""
    from .models import GebaeudewaermeData
    from .ui_provenance_service import load_ui_provenance_override_map, payload_for_row
    
    # Get all building heat data from database
    gebaeudewaerme_data = list(GebaeudewaermeData.objects.all())
    provenance_map = load_ui_provenance_override_map("gebaeudewaerme", gebaeudewaerme_data)
    
    # Convert to list of dictionaries with natural sorting
    data = []
    for item in gebaeudewaerme_data:
        if item.is_calculated:
            display_status = item.calculate_value() or None  # Will be None until formulas implemented
            display_ziel = item.calculate_ziel_value() or None  # Will be None until formulas implemented
        else:
            # For fixed items, show database values
            display_status = item.status
            display_ziel = item.ziel
        provenance = payload_for_row(item, "gebaeudewaerme", provenance_map)
        
        if "Alternativ zur" in item.category and "Brennstoffzellen (FC)" in item.category:
            from django.utils.safestring import mark_safe
            if item.user_percent == 100.0:
                display_ziel = mark_safe('<span style="color: blue; font-weight: bold;">Aktiv</span>')
            else:
                display_ziel = mark_safe('<span style="color: green; font-weight: bold;">(Passiv)</span>')
        
        data.append({
            'code': item.code,
            'category': item.category,
            'unit': item.unit,
            'status': display_status,
            'ziel': display_ziel,
            'formula': item.formula,
            'user_percent': item.user_percent,
            'is_calculated': item.is_calculated,
            # §2.3 Phase A provenance fields
            'source_url': provenance['source_url'],
            'notes_assumption': provenance['notes_assumption'],
            'source_refs': provenance['source_refs'],
            'origin': provenance['origin'],
            'provenance_override_active': provenance['provenance_override_active'],
        })
    
    # Apply natural sorting (same as other modules)
    def natural_sort_key(item):
        """Natural sorting for hierarchical codes like 2.0, 2.1, 2.1.1, 2.2, etc."""
        parts = item['code'].split('.')
        return [int(part) for part in parts]
    
    data.sort(key=natural_sort_key)
    
    return render(request, 'simulator/gebaeudewaerme.html', {"data": data})
