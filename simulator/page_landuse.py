"""LandUse page views and helpers."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import CalculationRun, Formula, LandUse
from .ui_provenance_service import apply_ui_provenance_to_objects

def get_landuse_data():
    """Get LandUse data formatted for calculations"""
    data = {}
    landuse_items = LandUse.objects.all()

    for landuse in landuse_items:
        if landuse.status_ha is not None:
            data[landuse.code] = float(landuse.status_ha)

    if "3.1" in data:
        data["ORIGINAL_3.1"] = data["3.1"]

    # Apply water mapping: 3.1 → 0 (for water calculations)
    if "0" in data and "3.1" in data:
        data["3.1"] = data["0"]  # Water uses total land area

    return data

def calculate_percentages(landuse):
    """
    Calculate percentages and ratios dynamically.
    Uses database formulas when available (extensible), with safe fallback to direct calculation.
    """
    data = {
        'landuse': landuse,
        'status_percent': None,
        'target_percent': None,
        'change_ratio': None,
    }

    # Calculate status percentage (child/parent)
    if landuse.parent and landuse.parent.status_ha and landuse.status_ha and landuse.parent.status_ha > 0:
        try:
            formula = Formula.objects.filter(key='LANDUSE_STATUS_PERCENT', category='landuse', is_active=True).first()
            if formula:
                context = {
                    'child_status': landuse.status_ha,
                    'parent_status': landuse.parent.status_ha,
                }
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['status_percent'] = round(result, 1)
            else:
                data['status_percent'] = round((landuse.status_ha / landuse.parent.status_ha) * 100, 1)
        except Exception:
            data['status_percent'] = round((landuse.status_ha / landuse.parent.status_ha) * 100, 1)

    # Calculate target percentage (child/parent)
    if landuse.parent and landuse.parent.target_ha and landuse.target_ha and landuse.parent.target_ha > 0:
        try:
            formula = Formula.objects.filter(key='LANDUSE_TARGET_PERCENT', category='landuse', is_active=True).first()
            if formula:
                context = {
                    'child_target': landuse.target_ha,
                    'parent_target': landuse.parent.target_ha,
                }
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['target_percent'] = round(result, 1)
            else:
                data['target_percent'] = round((landuse.target_ha / landuse.parent.target_ha) * 100, 1)
        except Exception:
            data['target_percent'] = round((landuse.target_ha / landuse.parent.target_ha) * 100, 1)

    # Calculate change ratio (target/status)
    if landuse.status_ha and landuse.target_ha and landuse.status_ha > 0:
        try:
            formula = Formula.objects.filter(key='LANDUSE_CHANGE_RATIO', category='landuse', is_active=True).first()
            if formula:
                context = {
                    'child_status': landuse.status_ha,
                    'child_target': landuse.target_ha,
                }
                result = eval(formula.expression, {"__builtins__": {}}, context)
                data['change_ratio'] = round(result, 2)
            else:
                data['change_ratio'] = round(landuse.target_ha / landuse.status_ha, 2)
        except Exception:
            data['change_ratio'] = round(landuse.target_ha / landuse.status_ha, 2)

    return data

@login_required
def landuse_list(request):
    """Display all land use data with calculations done in web app"""
    landuses = list(LandUse.objects.all().order_by('code'))
    apply_ui_provenance_to_objects(landuses, "landuse")
    latest_run = CalculationRun.objects.first()

    landuse_data = []
    for landuse in landuses:
        landuse_data.append(calculate_percentages(landuse))

    context = {
        'landuse_data': landuse_data,
        'total_count': len(landuses),
        'current_section': 'landuse',
        'latest_run': latest_run,
    }
    return render(request, 'simulator/landuse_list.html', context)

@login_required
def landuse_detail(request, pk):
    """Display detailed view of a specific land use item"""
    landuse = LandUse.objects.get(pk=pk)
    apply_ui_provenance_to_objects([landuse], "landuse")
    data = calculate_percentages(landuse)

    children = list(landuse.children.all())
    apply_ui_provenance_to_objects(children, "landuse")
    children_data = []
    for child in children:
        children_data.append(calculate_percentages(child))

    context = {
        'data': data,
        'children_data': children_data,
    }
    return render(request, 'simulator/landuse_detail.html', context)
