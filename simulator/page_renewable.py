"""Renewable/annual electricity page views."""

import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from simulator.signals import compute_ws_diagram_reference, get_ws_constants
from simulator.ws_365_service import get_ws_365_data
from simulator.ws_api import (
    _build_ws_columns,
    _compute_ws_daily_min_max,
    _build_ws_row_cells,
    _build_ws_summary_cells,
)

from .models import CalculationRun, CategoryDisplayName, Formula, RenewableData

def natural_sort_key(code):
    """
    Create a natural sorting key for codes like 1, 2, 3, ... 9, 10, 10.1, etc.
    Converts "10.1.2" to [10, 1, 2] for proper numerical sorting
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(code))]

@login_required
def renewable_list(request):
    """Display all renewable energy data with hierarchical structure - using stored values for speed"""

    renewables = list(RenewableData.objects.all())
    latest_run = CalculationRun.objects.first()
    run_id = request.GET.get("run_id")

    renewables.sort(key=lambda x: natural_sort_key(x.code))

    formula_keys = set(
        Formula.objects.filter(category='renewable', is_active=True)
        .values_list('key', flat=True)
    )

    hierarchical_data = []
    data_groups = {}

    for renewable in renewables:
        code_parts = renewable.code.split('.')
        hierarchy_level = len(code_parts)

        has_status_formula = renewable.code in formula_keys
        has_target_formula = any(
            key in formula_keys
            for key in (f"{renewable.code}_target", f"{renewable.code}_ziel_target", f"{renewable.code}_ziel")
        )
        is_calculated = has_status_formula or has_target_formula

        display_value = renewable.status_value
        display_target = renewable.target_value

        item = {
            'code': renewable.code,
            'name': renewable.name,
            'unit': renewable.unit,
            'hierarchy_level': hierarchy_level,
            'display_value': display_value,
            'display_target': display_target,
            'calculated_value': display_value if is_calculated else None,
            'is_fixed': renewable.is_fixed,
            'parent_code': '.'.join(code_parts[:-1]) if len(code_parts) > 1 else None,
            'formula': renewable.formula,
            'landuse_source': renewable.landuse_code if hasattr(renewable, 'landuse_code') else None,
            'landuse_code': renewable.landuse_code if hasattr(renewable, 'landuse_code') else None,
            'user_editable': renewable.user_editable,
            'user_input_value': renewable.user_input if renewable.user_input is not None else renewable.target_value,
        }
        hierarchical_data.append(item)

        category = code_parts[0]
        if category not in data_groups:
            data_groups[category] = []
        data_groups[category].append(renewable)

    context = {
        'hierarchical_data': hierarchical_data,
        'data_groups': data_groups,
        'total_count': len(renewables),
        'title': CategoryDisplayName.get_display_name('renewable'),
        'latest_run': latest_run,
        'run_id': run_id,
    }

    return render(request, 'simulator/renewable_list.html', context)

@login_required
def annual_electricity_view(request):
    """Annual electricity section using DB-driven formulas (category='annual')."""
    ws_consts = get_ws_constants()
    diagram = compute_ws_diagram_reference()

    pv_value = diagram['pv_value']
    wind_value = diagram['wind_value']
    bio_value = diagram['bio_value']
    hydro_value = diagram['hydro_value']
    m_total = diagram['m_total']
    ely_branch_value = diagram['ely_branch_value']
    n_value = diagram['n_value']
    n_input_branch = diagram['n_input_branch']
    n_output_branch = diagram['n_output_branch']
    gas_storage = diagram['gas_storage']
    storage_capacity = diagram['storage_capacity']
    t_value = diagram['t_value']
    t_output = diagram['t_output']
    n_to_right = diagram['n_to_right']
    final_stromnetz = diagram['final_stromnetz']
    h2_offer = diagram['h2_offer']
    h2_surplus = diagram['h2_surplus']
    eta_ely_pct = ws_consts['ETA_STROM_GAS'] * 100
    eta_es_pct = ws_consts['ETA_STROM_GAS'] * 100
    eta_rs_pct = ws_consts['ETA_GAS_STROM'] * 100
    eta_storage_pct = (t_output / n_output_branch * 100) if n_output_branch else 0
    solarstrom_366 = diagram['solarstrom_366']
    windstrom_366 = diagram['windstrom_366']
    sonst_kraft_konstant_366 = diagram['sonst_kraft_konstant_366']
    ws_data = get_ws_365_data(run_goal_seek=False)
    daily_data = ws_data.get('daily_data', [])
    ws_columns = _build_ws_columns(daily_data)
    ws_fields = [col["key"] for col in ws_columns if not col.get("is_day")]
    ws_min_row, ws_max_row = _compute_ws_daily_min_max(daily_data, ws_fields)
    ws_table_rows = [_build_ws_row_cells(row, ws_columns) for row in daily_data]
    ws_min_cells = _build_ws_summary_cells(ws_min_row, ws_columns, "Min")
    ws_max_cells = _build_ws_summary_cells(ws_max_row, ws_columns, "Max")

    r941 = RenewableData.objects.get(code='9.4.1')
    if r941.target_value != final_stromnetz:
        r941.target_value = final_stromnetz
        r941.is_fixed = True
        r941.formula = None
        r941.save(skip_cascade=True)

    if request.user.is_staff:
        current_scope_key = "global"
    else:
        current_scope_key = f"user:{request.user.id}"
    active_scenario_scope = request.session.get("active_scenario_scope")
    active_scenario_name = request.session.get("active_scenario_name")
    active_scenario_updated_at = request.session.get("active_scenario_updated_at")
    if active_scenario_scope == current_scope_key and active_scenario_name:
        diagram_scenario_label = active_scenario_name
        diagram_generated_on = active_scenario_updated_at or timezone.localtime().strftime('%d.%m.%Y %H:%M')
    else:
        diagram_scenario_label = 'Aktuelles Szenario'
        diagram_generated_on = timezone.localdate().strftime('%d.%m.%Y')

    context = {
        'current_section': 'annual_electricity',
        'title': 'Annual Electricity Analysis',
        'diagram_title': 'Jahresbilanz Strom',
        'diagram_scenario_label': diagram_scenario_label,
        'diagram_generated_on': diagram_generated_on,
        'bio': round(bio_value, 2),
        'pv': round(pv_value, 2),
        'wind': round(wind_value, 2),
        'hydro': round(hydro_value, 2),
        'm_total': round(m_total, 2),
        'ely_branch_value': round(ely_branch_value, 2),
        'ely_offer': round(ely_branch_value, 2),
        'gasspeicher_direkt': round(ely_branch_value * ws_consts['ETA_STROM_GAS'], 2),
        # T54 D1 — source Tagesladungen (formula confirmed from WS.xlsm 2026-04-23).
        'pv_tages': round(diagram.get('pv_tages', 397), 0),
        'wind_tages': round(diagram.get('wind_tages', 186), 0),
        'hydro_tages': round(diagram.get('hydro_tages', 5), 0),
        'bio_tages': round(diagram.get('bio_tages', 1), 0),
        # T54 D2 — flow Tagesladungen
        'flow_n_value_tages': round(diagram.get('flow_n_value_tages', 509), 0),
        'flow_q_abregelung_tages': round(diagram.get('flow_q_abregelung_tages', 62), 0),
        'flow_n_to_right_tages': round(diagram.get('flow_n_to_right_tages', 313), 0),
        'flow_final_tages': round(diagram.get('flow_final_tages', 365), 0),
        'flow_ely_branch_tages': round(diagram.get('flow_ely_branch_tages', 134), 0),
        'flow_n_output_branch_tages': round(diagram.get('flow_n_output_branch_tages', 134), 0),
        'flow_gasspeicher_direkt_tages': round(diagram.get('flow_gasspeicher_direkt_tages', 87), 0),
        'flow_gas_storage_tages': round(diagram.get('flow_gas_storage_tages', 87), 0),
        'flow_t_value_tages': round(diagram.get('flow_t_value_tages', 87), 0),
        'flow_reconversion_tages': round(diagram.get('flow_reconversion_tages', 51), 0),
        'flow_storage_capacity_tages': round(diagram.get('flow_storage_capacity_tages', 80), 0),
        # T54 D3 — percent shares
        'pv_pct': round(diagram.get('pv_pct', 62.2), 1),
        'wind_pct': round(diagram.get('wind_pct', 29.2), 1),
        'hydro_pct': round(diagram.get('hydro_pct', 0.8), 1),
        'bio_pct': round(diagram.get('bio_pct', 0.2), 1),
        # T54 D4c — Abgleichdifferenz
        'abgleichdifferenz': round(diagram.get('abgleichdifferenz', 160), 0),
        'abgleichdifferenz_tages': round(diagram.get('abgleichdifferenz_tages', 0), 0),
        'n_value': round(n_value, 2),
        'q_abregelung': round(diagram['q_abregelung'], 2),
        'n_input_branch': round(n_input_branch, 2),
        'n_output_branch': round(n_output_branch, 2),
        'ely_surplus': round(n_output_branch, 2),
        'n_to_right': round(n_to_right, 2),
        'h2_offer': round(h2_offer, 2),
        'h2_surplus': round(h2_surplus, 2),
        'gas_storage': round(gas_storage, 2),
        'storage_capacity': round(storage_capacity, 2),
        'eta_ely_pct': eta_ely_pct,
        'eta_es_pct': eta_es_pct,
        'eta_rs_pct': eta_rs_pct,
        'eta_storage_pct': eta_storage_pct,
        't_value': round(t_value, 2),
        't_output': round(t_output, 2),
        'final_stromnetz': round(final_stromnetz, 2),
        'n_input': round(n_input_branch, 2),
        'n_output': round(n_output_branch, 2),
        'h2_to_reconv': round(t_value, 2),
        'reconversion': round(t_output, 2),
        'final_consumption': round(final_stromnetz, 2),
        'solarstrom_366': round(solarstrom_366, 2),
        'windstrom_366': round(windstrom_366, 2),
        'sonst_kraft_konstant_366': round(sonst_kraft_konstant_366, 2),
        'daily_data': daily_data,
        'ws_columns': ws_columns,
        'ws_table_rows': ws_table_rows,
        'ws_min_cells': ws_min_cells,
        'ws_max_cells': ws_max_cells,
    }

    return render(request, 'simulator/annual_electricity.html', context)
