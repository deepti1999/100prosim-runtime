"""Historie page.

This page renders a prepared Excel-style comparison structure. Status and Ziel
values are read from the saved baseline and from the active/latest scenario.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .baseline_api import ADMIN_BASELINE_KEY
from .models import BaselineSnapshot, LandUse, RenewableData, ScenarioSnapshot, VerbrauchData


HISTORY_VALUE_SOURCES = {
    "15": ("renewable", "9.4.2"),
    "16": ("renewable", "9.2"),
    "18": ("renewable", "9.2.1.5.2.2"),
    "19": ("renewable", "9.2.1.5.2"),
    "22": ("verbrauch", "2.1.1"),
    "23": ("verbrauch", "2.2.1"),
    "26": ("verbrauch", "2.4.1"),
    "30": ("renewable", "7.1.2.2"),
    "31": ("renewable", "7.1.4.2"),
    "33": ("renewable", "4.1.3.1"),
    "34": ("renewable", "4.1.3"),
    "35": ("verbrauch", "2.10"),
    "37": ("renewable", "1.1.1.1.2"),
    "40": ("landuse", "LU_1"),
    "42": ("verbrauch", "4.1.1.1"),
    "43": ("verbrauch", "4.1.2"),
    "44": ("verbrauch", "5.1"),
    "46": ("verbrauch", "4.1.1.5"),
    "47": ("verbrauch", "4.1.1.15.1"),
    "48": ("verbrauch", "4.1.2.5"),
    "49": ("verbrauch", "4.1.2.15.1"),
    "51": ("verbrauch", "3.2.1"),
    "52": ("verbrauch", "1.3.2"),
    "53": ("verbrauch", "1.3.2"),
    "54": ("verbrauch", "3.4"),
    "55": ("renewable", "9.2.1.1"),
    "57": ("verbrauch", "9.1.1"),
    "58": ("renewable", "9.2.1.4.2"),
    "61": ("landuse", "LU_1.1"),
    "62": ("renewable", "1.1.1.1"),
    "64": ("landuse", "LU_1"),
    "65": ("renewable", "1.1.2.1.2.2"),
    "67": ("landuse", "LU_2.1"),
    "68": ("landuse", "LU_2"),
    "69": ("renewable", "1.2.1.2.2"),
    "72": ("landuse", "LU_6"),
    "73": ("landuse", "LU_0"),
    "74": ("renewable", "2.1.1.2"),
    "75": ("renewable", "2.2.1"),
    "77": ("renewable", "4.1.1.1.1"),
    "78": ("renewable", "4.2.1.1"),
    "80": ("landuse", "LU_2.2.2"),
    "81": ("landuse", "LU_2.2.3"),
    "82": ("landuse", "LU_2.2.4"),
    "83": ("landuse", "LU_2.2.5"),
    "84": ("landuse", "LU_2"),
    "87": ("renewable", "5.1.1"),
    "88": ("renewable", "9.3.3"),
    "90": ("verbrauch", "1.1.2"),
    "91": ("verbrauch", "1.2.2"),
    "92": ("verbrauch", "1.2.4"),
    "93": ("verbrauch", "1.3.2"),
    "94": ("verbrauch", "1.3.4"),
    "96": ("verbrauch", "1.4"),
    "97": ("verbrauch", "2.10"),
    "98": ("verbrauch", "3.7"),
    "99": ("verbrauch_split", "9.1.2", "9.1.4"),
    "100": ("verbrauch", "6.0"),
    "102": ("renewable", "2.1.1.2.2"),
    "103": ("renewable", "2.2.1.2.3"),
    "104": ("renewable", "9.1.2"),
    "105": ("renewable", "9.1.3"),
    "106": ("renewable", "10.9.1.1"),
    "107": ("renewable", "10.9.1.2"),
    "108": ("renewable", "10.9.1.3"),
    "109": ("renewable", "1.1.1.1.2"),
    "110": ("renewable", "7.1.2.3"),
    "111": ("renewable", "7.1.4.3"),
}

PASSIVE_VERBRAUCH_CODES = {"4.1.1.15.1", "4.1.2.15.1"}


HISTORY_TABLE_ROWS = [
    {"type": "section", "label": "Randbedingungen"},
    {
        "row_no": "8",
        "code": "Ra.",
        "label": "Bevölkerungsentwicklung",
        "unit": "Status +/- %",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "9",
        "code": "",
        "label": "Bevölkerungszahl",
        "unit": "",
        "level": 1,
        "strong": True,
        "status_value": "84.669.326",
        "target_value": "84.669.326",
    },
    {"type": "spacer"},
    {
        "row_no": "14",
        "code": "Rc.",
        "label": "Import Strom (erneuerbar)",
        "unit": "% zu Eigenerz.",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "15",
        "code": "",
        "label": "",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "16",
        "code": "",
        "label": "Bruttostromerzeug. erneuerb. in D",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "17",
        "code": "",
        "label": "Importwasserstoff - Stromeinsatz",
        "unit": "% v. Gesamt",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "18",
        "code": "",
        "label": "",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "19",
        "code": "",
        "label": "Stromeinsatz Wasserstoff gesamt",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {"type": "section", "label": "Gebäude"},
    {
        "row_no": "21",
        "code": "Ga.",
        "label": "Wohnfläche / Kopf",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "22",
        "code": "",
        "label": "",
        "unit": "m² / Kopf",
        "level": 1,
    },
    {
        "row_no": "23",
        "code": "",
        "label": "Gewerbefläche / Kopf",
        "unit": "% v. Status",
        "level": 1,
        "strong": True,
    },
    {"type": "spacer"},
    {
        "row_no": "25",
        "code": "Gb.",
        "label": "En. Gebäude-Sanierungsstandard",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "26",
        "code": "",
        "label": "",
        "unit": "kWh / (m² * a)",
        "level": 1,
    },
    {
        "row_no": "27",
        "code": "",
        "label": "Anteil En. Sanierter Gebäude",
        "unit": "% v. Bestand",
        "level": 0,
        "strong": True,
    },
    {"type": "spacer"},
    {
        "row_no": "29",
        "code": "Gc.",
        "label": "Wärmepumpenanteil an Gebäudew.",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "30",
        "code": "",
        "label": "Luftgekoppelte WP",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "31",
        "code": "",
        "label": "Erdreichgekoppelte WP",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "32",
        "code": "",
        "label": "Anteil Biobrennstoff an Geb.W.",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "33",
        "code": "",
        "label": "Anteil Energieholz zur Deckung",
        "unit": "% v. Gesamt",
        "level": 1,
    },
    {
        "row_no": "34",
        "code": "",
        "label": "Energieholz gesamt",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "35",
        "code": "",
        "label": "Gebäudewärme gesamt",
        "unit": "GWh/a",
        "level": 1,
    },
    {
        "row_no": "36",
        "code": "",
        "label": "Solarthermieanteil an Gebäudew.",
        "unit": "% v. Gesamt",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "37",
        "code": "",
        "label": "",
        "unit": "GWh",
        "level": 1,
    },
    {
        "row_no": "38",
        "code": "",
        "label": "Solarthermisch genutzte Fläche",
        "unit": "% GF",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "39",
        "code": "",
        "label": "",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "40",
        "code": "",
        "label": "Gebäude-&Freifläche",
        "unit": "ha",
        "level": 1,
    },
    {"type": "section", "label": "Verkehr"},
    {
        "row_no": "42",
        "code": "Va.",
        "label": "Personenverkehrsleistung /Kopf",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "43",
        "code": "&",
        "label": "Güterverkehrsleistung / Kopf",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "44",
        "code": "Vb.",
        "label": "Luftverkehrsleistung / Kopf",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {"type": "spacer"},
    {
        "row_no": "46",
        "code": "Vc.",
        "label": "Anteil Elektroakt. Personenverkehr",
        "unit": "% PVk-Leist",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "47",
        "code": "",
        "label": "Brennstoffzellen statt Verbrenner",
        "unit": "",
        "level": 1,
    },
    {
        "row_no": "48",
        "code": "",
        "label": "Anteil Elektroakt. Güterverkehr",
        "unit": "% GVk-Leist.",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "49",
        "code": "",
        "label": "Brennstoffzellen statt Verbrenner",
        "unit": "",
        "level": 1,
    },
    {"type": "section", "label": "Produktion (Güter)"},
    {
        "row_no": "51",
        "code": "Pa.",
        "label": "Prozesswärme Bedarfsniveau",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "52",
        "code": "",
        "label": "Industriestrom Bedarfsniveau",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "53",
        "code": "",
        "label": "Handel-/Gewerbestrom Bedarfsniveau",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "54",
        "code": "Pb.",
        "label": "Brennstoffanteil an Prozesswärme",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "55",
        "code": "",
        "label": "Wind-/Solarwasserstoff-Einsatz",
        "unit": "GWh/a",
        "level": 1,
    },
    {"type": "spacer"},
    {
        "row_no": "57",
        "code": "Pc.",
        "label": "Kunststofferzeugung / Kopf",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "58",
        "code": "",
        "label": "Wind-/Solarwasserstoff-Einsatz",
        "unit": "GWh/a",
        "level": 1,
    },
    {"type": "section", "label": "Erzeugung (Energie)"},
    {
        "row_no": "60",
        "code": "Ea.",
        "label": "Solare Dachflächen",
        "unit": "% v. GF",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "61",
        "code": "",
        "label": "",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "62",
        "code": "",
        "label": "davon Solarthermie",
        "unit": "%",
        "level": 1,
    },
    {
        "row_no": "63",
        "code": "",
        "label": "",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "64",
        "code": "",
        "label": "Gebäude-&Freifläche",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "65",
        "code": "",
        "label": "PV-Leistung installiert",
        "unit": "MW",
        "level": 1,
    },
    {
        "row_no": "66",
        "code": "",
        "label": "Solare Freiflächen",
        "unit": "% LF",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "67",
        "code": "",
        "label": "",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "68",
        "code": "",
        "label": "Landwirtschaftsfläche",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "69",
        "code": "",
        "label": "PV-Leistung installiert",
        "unit": "MW",
        "level": 1,
    },
    {"type": "spacer"},
    {
        "row_no": "71",
        "code": "Eb.",
        "label": "Windparkflächen onshore",
        "unit": "% BF",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "72",
        "code": "",
        "label": "",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "73",
        "code": "",
        "label": "Bodenfläche gesamt",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "74",
        "code": "",
        "label": "WEA-Leistung installiert",
        "unit": "MW",
        "level": 1,
    },
    {
        "row_no": "75",
        "code": "",
        "label": "WEA offshore-Leistung installiert",
        "unit": "MW",
        "level": 1,
    },
    {"type": "spacer"},
    {
        "row_no": "77",
        "code": "Ec.",
        "label": "Holz energetisch / Zuwachs",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "78",
        "code": "",
        "label": "Stroh energetisch / Anfall",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "79",
        "code": "",
        "label": "Energiepflanzen-Anbaufläche",
        "unit": "% LF",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "80",
        "code": "",
        "label": "für Biogas",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "81",
        "code": "",
        "label": "für Pflanzenöl",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "82",
        "code": "",
        "label": "für Bioethanol",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "83",
        "code": "",
        "label": "für Kurzumtrieb",
        "unit": "ha",
        "level": 1,
    },
    {
        "row_no": "84",
        "code": "",
        "label": "Landwirtschaftsfläche",
        "unit": "ha",
        "level": 1,
    },
    {"type": "spacer"},
    {
        "row_no": "86",
        "code": "",
        "label": "Biogas-Flächenertrag",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "87",
        "code": "",
        "label": "",
        "unit": "MWh/ha/a",
        "level": 1,
    },
    {"type": "spacer"},
    {
        "row_no": "88",
        "code": "",
        "label": "Stromspeicherkapaz. (Wasserst.)",
        "unit": "GWh",
        "level": 0,
        "strong": True,
    },
    {"type": "section", "label": "Klassische Stromanwendungen (KLIK)"},
    {
        "row_no": "90",
        "code": "",
        "label": "Stromanwend.-Effizienz Haushalte",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "91",
        "code": "",
        "label": "Handels-/Dienstleistungsvol./Pers.",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "92",
        "code": "",
        "label": "Stromanw.-Effiz.Handel/Dienstl.",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "93",
        "code": "",
        "label": "Industrie-Materialdurchsatz/Pers.",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "94",
        "code": "",
        "label": "Stromanw.-Effiz.Gewerbe/Industrie",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {"type": "section", "label": "Endenergie nach Anwendungsbereichen"},
    {
        "row_no": "96",
        "code": "",
        "label": "KLIK",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "97",
        "code": "",
        "label": "Gebäudewärme",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "98",
        "code": "",
        "label": "Prozesswärme",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "99",
        "code": "",
        "label": "Grundstoffe",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "100",
        "code": "",
        "label": "Mobile Antriebe",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {"type": "section", "label": "Primärenergie-Beiträge nach Quellen"},
    {
        "row_no": "102",
        "code": "",
        "label": "Windstrom onshore",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "103",
        "code": "",
        "label": "Windstrom offshore Regionalanteil",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "104",
        "code": "",
        "label": "Solarstrom",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "105",
        "code": "",
        "label": "Wasserkraft",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "106",
        "code": "",
        "label": "Biobrennstoffe gasförmig",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "107",
        "code": "",
        "label": "Biobrennstoffe flüssig",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "108",
        "code": "",
        "label": "Biobrennstoffe fest",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "109",
        "code": "",
        "label": "Solarwärme",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "110",
        "code": "",
        "label": "Umgebungswärme Luft",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "111",
        "code": "",
        "label": "Umgebungswärme Erdreich",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "112",
        "code": "",
        "label": "Fossile/atomare Brennstoffe",
        "unit": "GWh/a",
        "level": 0,
        "strong": True,
    },
    {"type": "section", "label": "Add on"},
    {
        "row_no": "114",
        "code": "",
        "label": "Wärmenanw.-Effiz.Gewerbe/Industrie",
        "unit": "% v. Status",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "115",
        "code": "",
        "label": "Syntheseanteil an Grundstoffen",
        "unit": "%",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "116",
        "code": "",
        "label": "Elektrolyseleistung (Stromspeicher.)",
        "unit": "GW",
        "level": 0,
        "strong": True,
    },
    {
        "row_no": "117",
        "code": "",
        "label": "Rückverstromungs-Leistung (elektr.)",
        "unit": "GW",
        "level": 0,
        "strong": True,
    },
]


def _format_history_number(value, unit):
    if value is None:
        return ""

    number = float(value)
    if abs(number) >= 1000 or unit in {"ha", "GWh/a", "GWh", "MW", "GW"}:
        return f"{number:,.0f}".replace(",", ".")

    rounded = round(number, 1)
    if rounded.is_integer():
        return f"{int(rounded)}"
    return f"{rounded:.1f}".replace(".", ",")


def _history_scope(request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_staff:
        return {"key": "global", "owner": None}
    if user and user.is_authenticated:
        return {"key": f"user:{user.id}", "owner": user}
    return {"key": "global", "owner": None}


def _scenario_scope_filter(owner):
    return {"owner__isnull": True} if owner is None else {"owner": owner}


def _payload_rows_by_code(payload, payload_key):
    return {
        str(row.get("code")): row
        for row in (payload or {}).get(payload_key, [])
        if row.get("code") is not None
    }


def _history_source_values_from_payload(payload, source_type, code, unit, target_code=None):
    if not payload:
        return "", ""

    if source_type == "renewable":
        row = _payload_rows_by_code(payload, "renewable").get(code)
        if row:
            return (
                _format_history_number(row.get("status_value"), unit),
                _format_history_number(row.get("target_value"), unit),
            )
    elif source_type == "verbrauch":
        row = _payload_rows_by_code(payload, "verbrauch").get(code)
        if row:
            if code in PASSIVE_VERBRAUCH_CODES and row.get("status") is None and row.get("ziel") is None:
                return "-", "(Passiv)"
            return (
                _format_history_number(row.get("status"), unit),
                _format_history_number(row.get("ziel"), unit),
            )
    elif source_type == "verbrauch_split":
        rows = _payload_rows_by_code(payload, "verbrauch")
        status_row = rows.get(code)
        target_row = rows.get(target_code)
        return (
            _format_history_number(status_row.get("status") if status_row else None, unit),
            _format_history_number(target_row.get("ziel") if target_row else None, unit),
        )
    elif source_type == "landuse":
        row = _payload_rows_by_code(payload, "landuse").get(code)
        if row:
            return (
                _format_history_number(row.get("status_ha"), unit),
                _format_history_number(row.get("target_ha"), unit),
            )

    return "", ""


def _history_source_values_from_live(source_type, code, unit, target_code=None):
    if source_type == "renewable":
        row = RenewableData.objects.filter(code=code).first()
        if row:
            return (
                _format_history_number(row.status_value, unit),
                _format_history_number(row.target_value, unit),
            )
    elif source_type == "verbrauch":
        row = VerbrauchData.objects.filter(code=code).first()
        if row:
            if code in PASSIVE_VERBRAUCH_CODES and row.status is None and row.ziel is None:
                return "-", "(Passiv)"
            return (
                _format_history_number(row.status, unit),
                _format_history_number(row.ziel, unit),
            )
    elif source_type == "verbrauch_split":
        status_row = VerbrauchData.objects.filter(code=code).first()
        target_row = VerbrauchData.objects.filter(code=target_code).first()
        return (
            _format_history_number(status_row.status if status_row else None, unit),
            _format_history_number(target_row.ziel if target_row else None, unit),
        )
    elif source_type == "landuse":
        row = LandUse.objects.filter(code=code).first()
        if row:
            return (
                _format_history_number(row.status_ha, unit),
                _format_history_number(row.target_ha, unit),
            )

    return "", ""


def _history_values_for_source(source, unit, payload=None, fallback_to_live=False):
    target_code = source[2] if source[0] == "verbrauch_split" else None
    values = _history_source_values_from_payload(
        payload,
        source[0],
        source[1],
        unit,
        target_code,
    )
    if fallback_to_live and values == ("", ""):
        values = _history_source_values_from_live(
            source[0],
            source[1],
            unit,
            target_code,
        )
    return values


@login_required
def historie_view(request):
    baseline_snapshot = BaselineSnapshot.objects.filter(key=ADMIN_BASELINE_KEY).first()
    baseline_payload = baseline_snapshot.payload if baseline_snapshot else None
    scope = _history_scope(request)
    scenarios = list(
        ScenarioSnapshot.objects
        .filter(**_scenario_scope_filter(scope["owner"]))
        .order_by("created_at", "id")
    )

    display_rows = []
    display_no = 1
    for row in HISTORY_TABLE_ROWS:
        row_copy = row.copy()
        if row_copy.get("type") not in {"section", "spacer"}:
            row_copy["display_no"] = display_no
            display_no += 1
            row_copy["baseline_status_value"] = row_copy.get("status_value", "")
            row_copy["baseline_target_value"] = row_copy.get("target_value", "")
            row_copy["scenario_values"] = [
                {
                    "status": row_copy.get("status_value", ""),
                    "target": row_copy.get("target_value", ""),
                }
                for _scenario in scenarios
            ]
            source = HISTORY_VALUE_SOURCES.get(row_copy["row_no"])
            if source:
                unit = row_copy.get("unit", "")
                baseline_status, baseline_target = _history_values_for_source(
                    source,
                    unit,
                    baseline_payload,
                    fallback_to_live=baseline_payload is None,
                )
                row_copy["baseline_status_value"] = baseline_status
                row_copy["baseline_target_value"] = baseline_target
                row_copy["scenario_values"] = []
                for scenario in scenarios:
                    scenario_status, scenario_target = _history_values_for_source(
                        source,
                        unit,
                        scenario.payload,
                        fallback_to_live=False,
                    )
                    row_copy["scenario_values"].append({
                        "status": scenario_status,
                        "target": scenario_target,
                    })

            if not scenarios:
                row_copy["scenario_values"] = [{
                    "status": row_copy.get("status_value", ""),
                    "target": row_copy.get("target_value", ""),
                }]
                if source:
                    current_status, current_target = _history_values_for_source(
                        source,
                        row_copy.get("unit", ""),
                        payload=None,
                        fallback_to_live=True,
                    )
                    row_copy["scenario_values"] = [{
                        "status": current_status,
                        "target": current_target,
                    }]
        display_rows.append(row_copy)

    context = {
        "history_rows": display_rows,
        "baseline_label": "Baseline" if baseline_snapshot else "Baseline nicht gespeichert",
        "scenario_columns": [
            {"label": scenario.name}
            for scenario in scenarios
        ] or [{"label": "Aktueller Stand"}],
        "history_colspan": 6 + 2 * (len(scenarios) or 1),
        "history_min_width_rem": 48 + 19 * (len(scenarios) or 1),
        "current_section": "historie",
    }
    return render(request, "simulator/historie.html", context)
