"""Bilanz page view."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from calculation_engine.bilanz_engine import calculate_bilanz_data

from .models import CalculationRun

@login_required
def bilanz_view(request):
    """
    Bilanz (Balance Sheet) View
    Compares supply (Aktiva: Renewable + Fossil) with demand (Passiva: Verbrauch)
    Structure: Erneuerbar + Fossil (Aktiva) = Verbrauch (Passiva)

    All calculations are dynamically pulled from RenewableData and VerbrauchData
    using the bilanz_engine calculation module.
    """

    bilanz_data = calculate_bilanz_data()
    bilanz_data['latest_run'] = CalculationRun.objects.first()

    ws_drift_tolerance = 0.1
    ws_balance_status = {
        'available': False,
        'is_balanced': False,
        'drift': 0.0,
        'day1': 0.0,
        'day365': 0.0,
        'min_ladezust': 0.0,
        'max_ladezust': 0.0,
        'deficit_days': 0,
        'tolerance': ws_drift_tolerance,
    }
    ws_chart_points = []

    from .ws_365_service import get_ws_365_data
    ws_data = get_ws_365_data(run_goal_seek=False)
    ws_current = ws_data['current']
    ws_daily = ws_data['daily_data']

    series = [float((row.get('ladezust_brutto') or 0.0)) for row in ws_daily]
    drift = float(ws_current['storage_drift'])
    day1 = float(ws_current['ladezust_day1'])
    day365 = float(ws_current['ladezust_day365'])

    ws_chart_points = [
        {
            'day': int(row.get('day') or idx + 1),
            'ladezust_brutto': float(row.get('ladezust_brutto') or 0.0),
        }
        for idx, row in enumerate(ws_daily)
    ]

    ws_balance_status = {
        'available': len(ws_chart_points) > 0,
        'is_balanced': abs(drift) <= ws_drift_tolerance,
        'drift': drift,
        'day1': day1,
        'day365': day365,
        'min_ladezust': min(series) if series else 0.0,
        'max_ladezust': max(series) if series else 0.0,
        'deficit_days': sum(1 for v in series if v < 0),
        'tolerance': ws_drift_tolerance,
    }

    bilanz_data['ws_balance_status'] = ws_balance_status
    bilanz_data['ws_chart_points'] = ws_chart_points
    bilanz_data['current_section'] = 'bilanz'

    return render(request, 'simulator/bilanz.html', bilanz_data)
