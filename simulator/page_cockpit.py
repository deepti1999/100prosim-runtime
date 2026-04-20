"""Cockpit dashboard page views."""

import json
import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import RenewableData, VerbrauchData

@login_required
def cockpit_view(request):
    """
    Cockpit dashboard with dynamic bar charts showing energy balance by sector.
    All data comes from bilanz_engine calculation module.
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from calculation_engine.bilanz_engine import calculate_bilanz_data

    try:
        bilanz_data = calculate_bilanz_data()

        def safe_get(data, *keys, default=0):
            try:
                result = data
                for key in keys:
                    result = result[key]
                return result if result is not None else default
            except (KeyError, TypeError):
                return default

        context = {
            'current_section': 'cockpit',
            'verbrauch_endenergie_gesamt': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'gesamt'),
            'verbrauch_endenergie_klik': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'kraft_licht'),
            'verbrauch_endenergie_gebaeudewaerme': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'gebaeudewaerme'),
            'verbrauch_endenergie_prozesswaerme': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'prozesswaerme'),
            'verbrauch_endenergie_mobile': safe_get(bilanz_data, 'verbrauch_gesamt', 'status', 'mobile'),
            'strom_total': safe_get(bilanz_data, 'verbrauch_strom', 'status', 'gesamt'),
            'strom_renewable': safe_get(bilanz_data, 'verbrauch_strom_renewable', 'status', 'gesamt'),
            'strom_fossil': safe_get(bilanz_data, 'verbrauch_strom_fossil', 'status', 'gesamt'),
            'brennstoffe_total': safe_get(bilanz_data, 'verbrauch_fuels', 'status', 'gesamt'),
            'brennstoffe_renewable': safe_get(bilanz_data, 'verbrauch_fuels_renewable', 'status', 'gesamt'),
            'brennstoffe_fossil': safe_get(bilanz_data, 'verbrauch_fuels_fossil', 'status', 'gesamt'),
            'brennstoffe_gaseous': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'gaseous'),
            'brennstoffe_liquid': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'liquid'),
            'brennstoffe_solid': safe_get(bilanz_data, 'fuels_breakdown', 'status', 'solid'),
            'waerme_total': safe_get(bilanz_data, 'verbrauch_heat', 'status', 'gesamt'),
            'waerme_renewable': safe_get(bilanz_data, 'verbrauch_heat_renewable', 'status', 'gesamt'),
            'waerme_fossil': safe_get(bilanz_data, 'verbrauch_heat_fossil', 'status', 'gesamt'),
            'renewable_klik': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'kraft_licht'),
            'renewable_gebaeudewaerme': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'gebaeudewaerme'),
            'renewable_prozesswaerme': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'prozesswaerme'),
            'renewable_mobile': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'status', 'mobile'),
            'verbrauch_endenergie_gesamt_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'gesamt'),
            'verbrauch_endenergie_klik_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'kraft_licht'),
            'verbrauch_endenergie_gebaeudewaerme_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'gebaeudewaerme'),
            'verbrauch_endenergie_prozesswaerme_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'prozesswaerme'),
            'verbrauch_endenergie_mobile_ziel': safe_get(bilanz_data, 'verbrauch_gesamt', 'ziel', 'mobile'),
            'strom_total_ziel': safe_get(bilanz_data, 'verbrauch_strom', 'ziel', 'gesamt'),
            'strom_renewable_ziel': safe_get(bilanz_data, 'verbrauch_strom_renewable', 'ziel', 'gesamt'),
            'strom_fossil_ziel': safe_get(bilanz_data, 'verbrauch_strom_fossil', 'ziel', 'gesamt'),
            'brennstoffe_total_ziel': safe_get(bilanz_data, 'verbrauch_fuels', 'ziel', 'gesamt'),
            'brennstoffe_renewable_ziel': safe_get(bilanz_data, 'verbrauch_fuels_renewable', 'ziel', 'gesamt'),
            'brennstoffe_fossil_ziel': safe_get(bilanz_data, 'verbrauch_fuels_fossil', 'ziel', 'gesamt'),
            'brennstoffe_gaseous_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'gaseous'),
            'brennstoffe_liquid_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'liquid'),
            'brennstoffe_solid_ziel': safe_get(bilanz_data, 'fuels_breakdown', 'ziel', 'solid'),
            'waerme_total_ziel': safe_get(bilanz_data, 'verbrauch_heat', 'ziel', 'gesamt'),
            'waerme_renewable_ziel': safe_get(bilanz_data, 'verbrauch_heat_renewable', 'ziel', 'gesamt'),
            'waerme_fossil_ziel': safe_get(bilanz_data, 'verbrauch_heat_fossil', 'ziel', 'gesamt'),
            'renewable_klik_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'kraft_licht'),
            'renewable_gebaeudewaerme_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'gebaeudewaerme'),
            'renewable_prozesswaerme_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'prozesswaerme'),
            'renewable_mobile_ziel': safe_get(bilanz_data, 'renewable_gesamt_by_sector', 'ziel', 'mobile'),
        }

        return render(request, 'simulator/cockpit.html', context)

    except Exception as e:
        import traceback
        return render(request, 'simulator/cockpit.html', {
            'current_section': 'cockpit',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'verbrauch_endenergie_gesamt': 0,
            'verbrauch_endenergie_klik': 0,
            'verbrauch_endenergie_gebaeudewaerme': 0,
            'verbrauch_endenergie_prozesswaerme': 0,
            'verbrauch_endenergie_mobile': 0,
            'strom_total': 0,
            'strom_renewable': 0,
            'strom_fossil': 0,
            'brennstoffe_total': 0,
            'brennstoffe_renewable': 0,
            'brennstoffe_fossil': 0,
            'brennstoffe_gaseous': 0,
            'brennstoffe_liquid': 0,
            'brennstoffe_solid': 0,
            'waerme_total': 0,
            'waerme_renewable': 0,
            'waerme_fossil': 0,
            'verbrauch_endenergie_gesamt_ziel': 0,
            'verbrauch_endenergie_klik_ziel': 0,
            'verbrauch_endenergie_gebaeudewaerme_ziel': 0,
            'verbrauch_endenergie_prozesswaerme_ziel': 0,
            'verbrauch_endenergie_mobile_ziel': 0,
            'strom_total_ziel': 0,
            'strom_renewable_ziel': 0,
            'strom_fossil_ziel': 0,
            'brennstoffe_total_ziel': 0,
            'brennstoffe_renewable_ziel': 0,
            'brennstoffe_fossil_ziel': 0,
            'brennstoffe_gaseous_ziel': 0,
            'brennstoffe_liquid_ziel': 0,
            'brennstoffe_solid_ziel': 0,
            'waerme_total_ziel': 0,
            'waerme_renewable_ziel': 0,
            'waerme_fossil_ziel': 0,
        })

def cockpit_view_old(request):
    """OLD VERSION - kept for reference"""

    def safe_get_values(obj, is_renewable=False):
        """Get status and target values safely"""
        try:
            if is_renewable:
                status, target = obj.get_calculated_values()
                return (status or 0, target or 0)
            else:
                status_strom = obj.get_effective_strom_value()
                status_gas = obj.get_effective_brennstoffe_gasfoermig_value()
                status_liquid = obj.get_effective_brennstoffe_fluessig_value()
                status_solid = obj.get_effective_brennstoffe_fest_value()
                status_heat = obj.get_effective_waerme_value()

                target_strom = obj.get_effective_strom_ziel_value()
                target_gas = obj.get_effective_brennstoffe_gasfoermig_ziel_value()
                target_liquid = obj.get_effective_brennstoffe_fluessig_ziel_value()
                target_solid = obj.get_effective_brennstoffe_fest_ziel_value()
                target_heat = obj.get_effective_waerme_ziel_value()

                status_total = status_strom + status_gas + status_liquid + status_solid + status_heat
                target_total = target_strom + target_gas + target_liquid + target_solid + target_heat

                return (status_total, target_total)
        except Exception:
            return (0, 0)

    categories_data = {
        'status': {},
        'ziel': {}
    }

    try:
        klik = VerbrauchData.objects.get(code='1.4')
        klik_s, klik_t = safe_get_values(klik)
        categories_data['status']['KLIK'] = klik_s
        categories_data['ziel']['KLIK'] = klik_t
    except Exception:
        categories_data['status']['KLIK'] = 0
        categories_data['ziel']['KLIK'] = 0

    try:
        gw = VerbrauchData.objects.get(code='2.9.0')
        gw_s, gw_t = safe_get_values(gw)
        categories_data['status']['Gebäudewärme'] = gw_s
        categories_data['ziel']['Gebäudewärme'] = gw_t
    except Exception:
        categories_data['status']['Gebäudewärme'] = 0
        categories_data['ziel']['Gebäudewärme'] = 0

    try:
        pw = VerbrauchData.objects.get(code='3.6.0')
        pw_s, pw_t = safe_get_values(pw)
        categories_data['status']['Prozesswärme'] = pw_s
        categories_data['ziel']['Prozesswärme'] = pw_t
    except Exception:
        categories_data['status']['Prozesswärme'] = 0
        categories_data['ziel']['Prozesswärme'] = 0

    try:
        mobile = VerbrauchData.objects.get(code='4.3.6')
        mobile_s, mobile_t = safe_get_values(mobile)
        categories_data['status']['Mobile'] = mobile_s
        categories_data['ziel']['Mobile'] = mobile_t
    except Exception:
        categories_data['status']['Mobile'] = 0
        categories_data['ziel']['Mobile'] = 0

    try:
        renewable = RenewableData.objects.get(code='10')
        ren_s, ren_t = safe_get_values(renewable, is_renewable=True)
        categories_data['status']['Erneuerbar'] = ren_s
        categories_data['ziel']['Erneuerbar'] = ren_t
    except Exception:
        categories_data['status']['Erneuerbar'] = 0
        categories_data['ziel']['Erneuerbar'] = 0

    total_verbrauch_status = sum([v for k, v in categories_data['status'].items() if k != 'Erneuerbar'])
    total_verbrauch_ziel = sum([v for k, v in categories_data['ziel'].items() if k != 'Erneuerbar'])

    categories_data['status']['Fossil'] = total_verbrauch_status - categories_data['status']['Erneuerbar']
    categories_data['ziel']['Fossil'] = total_verbrauch_ziel - categories_data['ziel']['Erneuerbar']

    context = {
        'current_section': 'cockpit',
        'title': 'Energieverbrauch Dashboard',
        'graph_data': categories_data,
        'graph_data_json': json.dumps(categories_data)
    }
    return render(request, 'simulator/cockpit.html', context)
