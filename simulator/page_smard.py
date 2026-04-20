"""SMARD visualization page."""

import os

import pandas as pd
from django.shortcuts import render

from .models import RenewableData, VerbrauchData

def smard_solar_wind(request):
    """SMARD data visualization for solar and wind energy"""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Actual_generation_202302010000_202401010000_Hour.csv')
    df = pd.read_csv(file_path, sep=';', decimal=',')
    df = df.replace('-', 0)

    def convert_to_float(value):
        if value == 0 or value == '0':
            return 0.0
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
            return float(value)
        return float(value)

    energy_columns = [
        'Photovoltaics [MWh] Calculated resolutions',
        'Wind onshore [MWh] Calculated resolutions',
        'Wind offshore [MWh] Calculated resolutions',
        'Hydropower [MWh] Calculated resolutions',
        'Biomass [MWh] Calculated resolutions',
        'Nuclear [MWh] Calculated resolutions',
        'Lignite [MWh] Calculated resolutions',
        'Hard coal [MWh] Calculated resolutions',
        'Fossil gas [MWh] Calculated resolutions'
    ]

    for col in energy_columns:
        df[col] = df[col].apply(convert_to_float)

    df['wind_total_MWh'] = df['Wind onshore [MWh] Calculated resolutions'] + df['Wind offshore [MWh] Calculated resolutions']
    df['total_demand_MWh'] = (
        df['Photovoltaics [MWh] Calculated resolutions'] +
        df['wind_total_MWh'] +
        df['Hydropower [MWh] Calculated resolutions'] +
        df['Biomass [MWh] Calculated resolutions'] +
        df['Nuclear [MWh] Calculated resolutions'] +
        df['Lignite [MWh] Calculated resolutions'] +
        df['Hard coal [MWh] Calculated resolutions'] +
        df['Fossil gas [MWh] Calculated resolutions']
    )

    df['Date'] = pd.to_datetime(df['Start date'])
    df['day'] = df['Date'].dt.date

    daily = df.groupby('day').agg({
        'Photovoltaics [MWh] Calculated resolutions': 'sum',
        'wind_total_MWh': 'sum',
        'Hydropower [MWh] Calculated resolutions': 'sum',
        'Biomass [MWh] Calculated resolutions': 'sum',
        'total_demand_MWh': 'sum'
    }).reset_index()

    daily = daily.rename(columns={
        'day': 'date',
        'Photovoltaics [MWh] Calculated resolutions': 'solar_smard_MWh',
        'wind_total_MWh': 'wind_smard_MWh',
        'Hydropower [MWh] Calculated resolutions': 'hydro_MWh',
        'Biomass [MWh] Calculated resolutions': 'bio_MWh',
        'total_demand_MWh': 'demand_MWh'
    })

    solar_total = daily['solar_smard_MWh'].sum()
    wind_total = daily['wind_smard_MWh'].sum()
    hydro_total = daily['hydro_MWh'].sum()
    bio_total = daily['bio_MWh'].sum()
    demand_total = daily['demand_MWh'].sum()

    daily['solar_pu'] = daily['solar_smard_MWh'] / solar_total if solar_total > 0 else 0
    daily['wind_pu'] = daily['wind_smard_MWh'] / wind_total if wind_total > 0 else 0
    daily['hydro_pu'] = daily['hydro_MWh'] / hydro_total if hydro_total > 0 else 0
    daily['bio_pu'] = daily['bio_MWh'] / bio_total if bio_total > 0 else 0
    daily['demand_pu'] = daily['demand_MWh'] / demand_total if demand_total > 0 else 0

    daily['solar_total_GWh'] = solar_total / 1000
    daily['wind_total_GWh'] = wind_total / 1000
    daily['hydro_total_GWh'] = hydro_total / 1000
    daily['bio_total_GWh'] = bio_total / 1000
    daily['demand_total_GWh'] = demand_total / 1000

    try:
        pv_target_record = RenewableData.objects.filter(code__icontains='solar').first() or \
                          RenewableData.objects.filter(code__icontains='photovoltaic').first() or \
                          RenewableData.objects.filter(code__icontains='pv').first()
        wind_target_record = RenewableData.objects.filter(code__icontains='wind').first()
        hydro_target_record = RenewableData.objects.filter(code__icontains='hydro').first() or \
                             RenewableData.objects.filter(code__icontains='water').first()
        bio_target_record = RenewableData.objects.filter(code__icontains='bio').first() or \
                           RenewableData.objects.filter(code__icontains='biomass').first()

        if not pv_target_record:
            raise ValueError("PV target record not found in database. Please import renewable data.")
        if not wind_target_record:
            raise ValueError("Wind target record not found in database. Please import renewable data.")
        if not hydro_target_record:
            raise ValueError("Hydro target record not found in database. Please import renewable data.")
        if not bio_target_record:
            raise ValueError("Bio target record not found in database. Please import renewable data.")

        PV_target_GWh = float(pv_target_record.ziel or pv_target_record.status or 0)
        Wind_target_GWh = float(wind_target_record.ziel or wind_target_record.status or 0)
        Hydro_target_GWh = float(hydro_target_record.ziel or hydro_target_record.status or 0)
        Bio_target_GWh = float(bio_target_record.ziel or bio_target_record.status or 0)

    except Exception as e:
        raise ValueError(f"Database missing renewable energy data. Please import data first. Error: {e}")

    PV_target_MWh = PV_target_GWh * 1000
    Wind_target_MWh = Wind_target_GWh * 1000
    Hydro_target_MWh = Hydro_target_GWh * 1000
    Bio_target_MWh = Bio_target_GWh * 1000

    daily['solar_scenario_MWh_day'] = daily['solar_pu'] * PV_target_MWh
    daily['wind_scenario_MWh_day'] = daily['wind_pu'] * Wind_target_MWh
    daily['hydro_scenario_MWh_day'] = Hydro_target_MWh / 365
    daily['bio_scenario_MWh_day'] = daily['bio_pu'] * Bio_target_MWh

    daily['ren_total_MWh_day'] = (
        daily['solar_scenario_MWh_day'] +
        daily['wind_scenario_MWh_day'] +
        daily['hydro_scenario_MWh_day'] +
        daily['bio_scenario_MWh_day']
    )

    calculated_total_MWh = daily['ren_total_MWh_day'].sum()
    expected_total_MWh = PV_target_MWh + Wind_target_MWh + Hydro_target_MWh + Bio_target_MWh
    daily['calculated_total_GWh'] = calculated_total_MWh / 1000
    daily['expected_total_GWh'] = expected_total_MWh / 1000
    daily['total_check_diff_percent'] = ((calculated_total_MWh - expected_total_MWh) / expected_total_MWh * 100) if expected_total_MWh > 0 else 0

    daily['PV_target_GWh'] = PV_target_GWh
    daily['Wind_target_GWh'] = Wind_target_GWh
    daily['Hydro_target_GWh'] = Hydro_target_GWh
    daily['Bio_target_GWh'] = Bio_target_GWh

    ren_sorted = daily['ren_total_MWh_day'].sort_values(ascending=False).reset_index(drop=True)

    try:
        electricity_total_entry = VerbrauchData.objects.filter(code='5').first()

        if electricity_total_entry:
            if electricity_total_entry.is_calculated:
                verbrauch_status_GWh = electricity_total_entry.calculate_value()
                verbrauch_ziel_GWh = electricity_total_entry.calculate_ziel_value()
            else:
                verbrauch_status_GWh = electricity_total_entry.status
                verbrauch_ziel_GWh = electricity_total_entry.ziel

            verbrauch_status_MWh_per_year = verbrauch_status_GWh * 1000
            verbrauch_ziel_MWh_per_year = verbrauch_ziel_GWh * 1000

            annual_demand_MWh = verbrauch_status_MWh_per_year
            daily_average_demand_MWh = annual_demand_MWh / 365

        else:
            raise ValueError("VerbrauchData Code 5 not found in database. Please import verbrauch data.")

    except Exception as e:
        raise ValueError(f"Database missing verbrauch energy data. Please import data first. Error: {e}")

    if daily['demand_MWh'].sum() > 0:
        smard_demand_shape = daily['demand_MWh'] / daily['demand_MWh'].sum()
        daily['verbrauch_demand_MWh'] = smard_demand_shape * annual_demand_MWh
    else:
        daily['verbrauch_demand_MWh'] = daily_average_demand_MWh

    dmd_sorted = daily['verbrauch_demand_MWh'].sort_values(ascending=False).reset_index(drop=True)

    daily['verbrauch_status_GWh'] = verbrauch_status_GWh if 'verbrauch_status_GWh' in locals() else 0
    daily['verbrauch_ziel_GWh'] = verbrauch_ziel_GWh if 'verbrauch_ziel_GWh' in locals() else 0
    daily['annual_demand_check_GWh'] = annual_demand_MWh / 1000 if 'annual_demand_MWh' in locals() else 0

    surplus_sorted = ren_sorted - dmd_sorted
    surplus_positive = surplus_sorted[surplus_sorted > 0]
    stromaufnahme_MWh = surplus_positive.sum()
    stromaufnahme_GWh = stromaufnahme_MWh / 1000

    daily['day_rank'] = range(1, len(daily) + 1)
    daily['ren_sorted_MWh'] = ren_sorted
    daily['dmd_sorted_MWh'] = dmd_sorted
    daily['surplus_sorted_MWh'] = surplus_sorted

    daily['stromaufnahme_MWh'] = stromaufnahme_MWh
    daily['stromaufnahme_GWh'] = stromaufnahme_GWh
    daily['surplus_days_count'] = len(surplus_positive)
    daily['total_days_count'] = len(surplus_sorted)
    daily['surplus_days_percent'] = (len(surplus_positive) / len(surplus_sorted) * 100) if len(surplus_sorted) > 0 else 0

    total_demand_check_MWh = daily['verbrauch_demand_MWh'].sum()
    daily['demand_verification_GWh'] = total_demand_check_MWh / 1000
    daily['demand_difference_percent'] = ((total_demand_check_MWh - annual_demand_MWh) / annual_demand_MWh * 100) if 'annual_demand_MWh' in locals() else 0

    data = daily.to_dict(orient='records')

    for record in data:
        if 'date' in record:
            record['date'] = record['date'].strftime('%Y-%m-%d')

    return render(request, 'simulator/smard_solar_wind.html', {'data': data})
