from __future__ import annotations

import html
import re

from django.core.management.base import BaseCommand, CommandError
from django.utils.html import strip_tags

from simulator.models import (
    GebaeudewaermeData,
    LandUse,
    Region,
    RenewableData,
    UIProvenanceOverride,
    UIProvenanceSource,
    VerbrauchData,
)
from simulator.templatetags.provenance_filters import render_provenance_note
from simulator.ui_provenance_service import split_notes_assumption_sections


DOMAIN_MODEL_MAP = {
    "landuse": LandUse,
    "renewable": RenewableData,
    "verbrauch": VerbrauchData,
    "gebaeudewaerme": GebaeudewaermeData,
}


RENEWABLE_MANUAL_OVERRIDE_CODES = {
    "4.1.2.1",
    "4.1.2.1.1",
    "4.1.2.1.2",
    "4.1.3",
    "4.1.3.4",
    "4.3.1",
    "4.3.2",
    "4.3.3",
    "4.3.3.1",
    "4.3.3.2",
    "4.3.3.3",
    "4.3.3.4",
    "4.3.4.2",
    "4.4.1",
    "4.4.2",
    "5.1.2",
    "5.2",
    "5.3",
    "5.4.2",
    "5.4.2.1",
    "5.4.2.2",
    "5.4.2.3",
    "5.4.3",
    "5.4.3.1",
    "5.4.3.2",
    "5.4.4.2",
    "6.1.1",
    "6.1.1.2",
    "6.1.2",
    "6.1.3",
    "6.1.3.1.1",
    "6.1.3.2",
    "6.1.3.2.2",
    "6.1.3.2.3",
    "6.2.1.2",
    "6.2.2",
    "7.1",
    "7.1.1",
    "7.1.2",
    "7.1.2.1",
    "7.1.2.2",
    "7.1.2.3",
    "7.1.3",
    "7.1.4",
    "7.1.4.1",
    "7.1.4.2",
    "7.1.4.3",
    "7.1.4.3.1",
    "7.1.4.3.2",
    "7.1.4.3.3",
    "7.1.4.3.4",
    "8.1",
    "8.1.1",
    "8.1.2",
    "8.2",
    "9.1",
    "9.2",
    "9.2.1",
    "9.2.1.1",
    "9.2.1.1.1",
    "9.2.1.1.1.1",
    "9.2.1.1.2",
    "9.2.1.2",
    "9.2.1.2.1",
    "9.2.1.2.2",
    "9.2.1.3",
    "9.2.1.3.1",
    "9.2.1.3.2",
    "9.2.1.4",
    "9.2.1.4.1",
    "9.2.1.4.2",
    "9.2.1.5",
    "9.2.1.5.1",
    "9.2.1.5.2",
    "9.2.1.5.2.1",
    "9.2.1.5.2.2",
    "9.3",
    "9.3.1",
    "9.3.2",
    "9.3.2.1",
    "9.3.3",
    "9.3.4",
    "9.4",
    "9.4.1",
    "9.4.2",
    "9.4.3",
    "9.4.3.1",
    "9.4.3.2",
    "9.4.3.3",
}


def _current_ui_note_text(row) -> str:
    """Backfill the admin form with the cleaned note text users already see.

    Imported workbook text may still contain internal Excel refs like
    [9.224]. The live UI already cleans those during rendering. Admin
    should start from that same cleaned text so edits are WYSIWYG.
    """
    raw_note = getattr(row, "notes_assumption", None)
    if not raw_note:
        return ""

    rendered = str(render_provenance_note(raw_note, getattr(row, "source_refs", None) or []))
    rendered = rendered.replace("<br><br>", "\n\n").replace("<br>", "\n")
    return html.unescape(strip_tags(rendered).strip())


def _normalize_text_fragment(text: str) -> str:
    text = (text or "").replace("#REF!", "").strip()
    text = text.replace("GENESIS 33111-01-02-4, Tabelle 33111-01-02-4", "GENESIS, Tabelle 33111-01-02-4")
    text = text.replace("DESTATIS 41121-0102.1 R, Tabelle 41121-0102.1 R", "DESTATIS, Tabelle 41121-0102.1 R")
    text = text.replace("FNR S. 17,46, S. 17,46", "FNR, S. 17, 46")
    text = text.replace("FNR S. 16, 19, S. 16, 19", "FNR, S. 16, 19")
    text = text.replace("FNR S. 19, S. 19", "FNR, S. 19")
    text = text.replace("Waldstrategie 2050 Waldstrategie 2050", "Waldstrategie 2050")
    text = text.replace("Wind Leistung (Land) Wind Leistung (Land)", "Wind Leistung (Land)")
    text = text.replace("S. 291 ff.S. 291 ff.S. 291 ff.S. 291 ff.S. 291 ff.S. 291 ff.", "S. 291 ff.")
    text = text.replace("S. 3, S. 3", "S. 3")
    text = text.replace("S. 13, 15 S. 13, 15", "S. 13, 15")
    text = text.replace("bis spätestens2050", "bis spätestens 2050")
    text = text.replace("Überinstimmung", "Übereinstimmung")
    text = text.replace("Potenzialläche", "Potenzialfläche")
    text = text.replace("Rotorduchmessern", "Rotordurchmessern")
    text = text.replace("Verkehswege", "Verkehrswege")
    text = text.replace("Emmissionen", "Emissionen")
    text = text.replace("betrachet", "betrachtet")
    text = text.replace("kritisich", "kritisch")
    text = text.replace("( ha in ).", "").replace("( ha in )", "")
    text = text.replace("  ", " ").replace(" \n", "\n")
    return "\n\n".join(part.strip() for part in text.split("\n\n") if part.strip())


def _clean_landuse_note_parts(row_code: str, note_parts: dict[str, str]) -> dict[str, str]:
    note_parts = {
        "general_information": _normalize_text_fragment(note_parts.get("general_information", "")),
        "status_information": _normalize_text_fragment(note_parts.get("status_information", "")),
        "ziel_information": _normalize_text_fragment(note_parts.get("ziel_information", "")),
    }

    row_specific = {
        "LU_1": {
            "ziel": (
                "Da der Flächenverbrauch für Siedlungszwecke vor allem zu Lasten der landwirtschaftlichen Flächen geht, "
                "kommt der Reduzierung des Flächenverbrauchs große Bedeutung zu. Aus einem restlichen Flächenverbrauch "
                "von 7,9 % der Siedlungs- und Verkehrsfläche erhöht sich die Siedlungsfläche bis spätestens 2050 auf "
                "3.645.799 ha. Das Erreichen einer Flächenkreislaufwirtschaft mit diesem Zielwert wird hier bereits "
                "für das Zieljahr 2045 angenommen.\n\n"
                "Gemäß UBA soll im Rahmen der Ressourcenstrategie der Europäischen Union und dem Klimaschutzplan der "
                "Bundesregierung bis spätestens 2050 der Übergang zur Flächenkreislaufwirtschaft (Netto-Null-Ziel) "
                "erreicht werden. Aus einer Siedlungs- und Verkehrsfläche von 5.190.300 ha und einem täglichen "
                "Flächenverbrauch von 52 ha im Jahr 2022 resultiert bei linearer Abnahme bis 0 ha pro Jahr in 2050 "
                "ein restlicher Flächenverbrauch von insgesamt 265.720 ha. Bezogen allein auf die Siedlungsfläche "
                "Deutschlands von 3.380.079 ha im Jahr 2022 sind das noch 7,9 %."
            ),
        },
        "LU_1.1": {
            "status": (
                "Die solare Absorberfläche auf Dächern von 34.243 ha resultiert aus der Summe von solarthermischen "
                "Flach- und Röhrenkollektoren zur Wärmegewinnung und Photovoltaikmodulen zur Stromgewinnung.\n\n"
                "Die solarthermischen Flach- und Röhrenkollektoren zur Wärmegewinnung belegten eine Fläche von "
                "2.178,5 ha. Sie werden hier komplett den Dachflächen zugerechnet, da sie zur Vermeidung von "
                "Verlusten beim Wärmetransport meist verbrauchsnah auf Gebäuden installiert sind.\n\n"
                "Insgesamt waren 2022 in Deutschland 47.857 MWp gebäudegebundene Photovoltaik installiert "
                "(2021: 42.685 MWp). Unter der Annahme einer Flächenleistung von 6,7 m²/kWp resultiert daraus "
                "eine PV-Modulfläche auf Dächern von 32.064 ha."
            ),
            "ziel": (
                "199.398 ha solare Absorberfläche auf Dächern. Der Wert resultiert aus einer Studie von Agora "
                "Energiewende nach Summierung der im Datenanhang als Photovoltaikpotenzial auf Dachflächen in "
                "Deutschland gelisteten Modulflächen. Dabei wurde unterstellt, dass diese Flächen alternativ auch "
                "als Kollektorflächen für Solarwärmegewinnung genutzt werden können.\n\n"
                "Im Datenteil der Agora-Studie werden 36 Millionen Gebäude in Deutschland nach ihrer Eignung der "
                "Dachflächen für Photovoltaik bewertet. Bei der Ermittlung des Modulflächenpotenzials wurden neben "
                "Dachfläche und Ausrichtung auch verschiedene Abschläge berücksichtigt (statisch ungeeignet, zu klein, "
                "Störflächen wie Dachfenster usw.). Für Deutschland resultiert daraus ein technisch geeignetes "
                "Dachflächenpotenzial von 199.398 ha."
            ),
        },
        "LU_2": {
            "ziel": (
                "Der Flächenverbrauch für Siedlungszwecke, einschließlich Verkehr, von 265.720 ha geht zu Lasten "
                "der Landwirtschaftsfläche, die sich entsprechend verringert. Eine weitere Ausweitung der Waldflächen "
                "zu Lasten der Landwirtschaftsflächen entsprechend dem Trend der zurückliegenden Zeit wird hier nicht "
                "angenommen.\n\n"
                "Der Ansatz erscheint aus Sicht der Ernährungssicherheit zukunftsfähig: Nach einer wissenschaftlichen "
                "Studie im Auftrag von Greenpeace würde zur Ernährung der Bevölkerung nach vollständiger Umstellung "
                "auf ökologische Wirtschaftsweise eine Landwirtschaftsfläche von 14.360.000 ha ausreichen, selbst "
                "ohne Umstellung auf eine flächenschonende Ernährung."
            ),
        },
        "LU_2.1": {
            "status": (
                "Solare Freiflächenanlagen dienen nahezu vollständig der Stromgewinnung mit Photovoltaikmodulen, "
                "da Solarthermie gewöhnlich verbrauchsnah auf Dachflächen erfolgt. Von der gesamten installierten "
                "PV-Leistung mit 67.596 MWp sind 19.530 MWp entsprechend 28,9 % auf Freiflächen installiert. "
                "Eine Modulfläche von 13.085 ha ergibt sich bei einem durchschnittlichen Modulflächenbedarf von "
                "6,7 m²/kWp. Zur Vermeidung gegenseitiger Abschattung sind Abstandsflächen erforderlich. Die Größe "
                "der beanspruchten Freiflächen liegt im Fall der heute üblichen Südausrichtung beim 1,5-Fachen der "
                "aufgestellten Modulfläche, das sind in diesem Fall 19.628 ha.\n\n"
                "\"Als Faustregel gilt, dass für eine PV-Freiflächenanlage mit 1.000 kWp eine Fläche von knapp unter "
                "einem Hektar notwendig ist.\" Das entspricht einer spezifischen Flächenbelegung von 10 m²/kWp und "
                "damit dem 1,5-Fachen der spezifischen Modulfläche von 6,7 m²/kWp."
            ),
            "ziel": (
                "Als Beitrag zur Deckung des Strombedarfs sind 666.100 ha PV-Freiflächenanlagen vorgesehen. "
                "Unter Beibehaltung der heutigen Südausrichtung entspricht das einer PV-Modulfläche von 444.067 ha. "
                "Bei Aufstellung in Ost-/West-Ausrichtung mit 10° Neigung läge der spezifische Flächenbedarf um den "
                "Faktor 2,5 niedriger; wegen der stärkeren Konzentration auf hohen Sonnenstand wäre dann allerdings "
                "der Bedarf an Langzeit-Stromspeicherkapazität erheblich größer. Das ist im aktuellen Softwarestand "
                "nicht modellierbar.\n\n"
                "ACHTUNG! Nach Szenario-Modifikationen in S.1.13 kann der Zielwert dort von diesem Standardansatz "
                "abweichen.\n\n"
                "Hinweis aus einer Stellungnahme des Instituts für Solarforschung Hameln: "
                "\"Für eine flächenoptimierte Energieerzeugung sollte ein flacher (z. B. 10°) Anstellwinkel und "
                "eine Ost-West-Richtung ausgewählt werden. Dies reduziert den Ertrag pro Solarmodul auf ca. 85 % "
                "(LK OS 2012). Der Flächenertrag steigt dadurch aber um einen Faktor 2,6 im Vergleich zur "
                "Südausrichtung, da die Solarmodule in geringerem Abstand zueinander montiert werden können.\" "
                "(Der Faktor 2,6 bezieht sich auf die Strahlungsverhältnisse in Niedersachsen. Auf deutsche "
                "Strahlungsverhältnisse übertragen handelt es sich um einen Faktor von 2,0.)"
            ),
        },
        "LU_2.2": {
            "ziel": (
                "10.826.000 ha resultieren aus der Annahme, dass die Abnahme der Landwirtschaftsfläche um 265.720 ha "
                "voll zu Lasten der Ackerfläche geht und dass 333.050 ha von der Hälfte der Freiflächen-Solaranlagen "
                "belegt werden. Dabei werden die Rahmenbedingungen der Landwirtschaft als bestenfalls konstant "
                "angenommen.\n\n"
                "Der Ansatz erscheint aus Sicht der Ernährungssicherheit zukunftsfähig: Nach einer wissenschaftlichen "
                "Studie im Auftrag von Greenpeace würde zur Ernährung der Bevölkerung nach vollständiger Umstellung "
                "auf ökologische Wirtschaftsweise eine Ackerfläche von 10.060.000 ha ausreichen, selbst ohne "
                "Umstellung auf eine flächenschonende Ernährung."
            ),
        },
        "LU_2.2.1": {
            "ziel": (
                "Da die Einflüsse auf die künftige Entwicklung der Getreideanbaufläche vielfältig, komplex und schwer "
                "einschätzbar sind, wird von einer Veränderung proportional zur Ackerlandfläche ausgegangen."
            ),
        },
        "LU_2.2.2": {
            "status": (
                "Nach FNR lag die Anbaufläche nachwachsender Rohstoffe für Biogas im Jahr 2022 mit 1.410.000 ha bei "
                "61 % der gesamten Energiepflanzen-Anbaufläche von 2.302.000 ha. Damit wurden 7,8 % der "
                "Landwirtschaftsfläche für die Biogasgewinnung beansprucht. Auf die Ackerfläche bezogen ergibt sich "
                "rechnerisch ein Anteil von 12,1 %. Allerdings wurde hier vereinfachend auch die durch Grassilage "
                "für Biogas beanspruchte Dauergrünlandfläche von 298.552 ha einbezogen. Netto wird somit lediglich "
                "eine Ackerfläche von 1.111.448 ha beansprucht; das entspricht einem Anteil von 9,5 %."
            ),
            "ziel": (
                "Innerhalb der Extrempositionen beim Anbau energetisch genutzter nachwachsender Rohstoffe geht der "
                "gewählte Ansatz vom Erhalt des Status quo beim Anteil der energetisch beanspruchten "
                "Landwirtschaftsfläche von 12,9 % aus. Von 2.287.789 ha resultierender Zielfläche bleibt nach Abzug "
                "der übrigen Nutzungen, also Pflanzenöl, Ethanol, Kurzumtrieb und der Hälfte der Freiflächen-PV, "
                "eine Anbaufläche für Biogas von 1.307.488 ha entsprechend 7,4 % der Landwirtschaftsfläche.\n\n"
                "Die komplexen Zusammenhänge zwischen Bioenergie-Anbaupotenzialen, Nahrungsmittelversorgung, "
                "Ernährungsgewohnheiten, Agrarimporten, Umweltgesichtspunkten und Nachhaltigkeit werden im Rahmen "
                "dieses Szenarios nicht vertieft, sondern nur in dieser Größenordnung berücksichtigt."
            ),
        },
        "LU_2.2.3": {
            "status": (
                "Nach FNR lag die Anbaufläche für Biodiesel im Jahr 2022 bei 665.000 ha. Das entspricht 25,6 % der "
                "gesamten Energiepflanzen-Anbaufläche von 2.595.000 ha, 5,7 % der Ackerfläche beziehungsweise 3,7 % "
                "der Landwirtschaftsfläche. Mit dem resultierenden Biodiesel von ca. 11.804 GWh pro Jahr lassen sich "
                "etwa zwei Drittel des Dieselbedarfs der deutschen Landwirtschaft in Höhe von ca. 19.400 GWh pro Jahr "
                "decken."
            ),
            "ziel": (
                "Innerhalb der Extrempositionen beim Anbau energetisch genutzter nachwachsender Rohstoffe geht der "
                "gewählte Ansatz von einer Halbierung der Pflanzenöl-Anbaufläche aus. Die angenommene Zielfläche von "
                "303.000 ha entspricht 1,7 % der Landwirtschaftsfläche. Die Minderung erfolgt zugunsten von Biogas "
                "wegen der mehrfach höheren Energieerträge. Mit dem Kraftstoff kann aber zumindest ein Teil des "
                "Verbrauchs landwirtschaftlicher Maschinen gedeckt werden."
            ),
        },
        "LU_2.2.4": {
            "status": (
                "Nach FNR lag die Anbaufläche für Bioethanol im Jahr 2022 bei 216.200 ha. Das entspricht 8,9 % der "
                "gesamten Energiepflanzen-Anbaufläche von 2.421.000 ha, 1,9 % der Ackerfläche beziehungsweise 1,2 % "
                "der Landwirtschaftsfläche."
            ),
        },
        "LU_2.2.5": {
            "status": (
                "Gemäß einer Studie des Von-Thünen-Instituts waren in Deutschland im Jahr 2022 11.200 ha Ackerfläche "
                "mit Kurzumtriebsplantagen einschließlich Miscanthus belegt. Hier wird konservativ davon ausgegangen, "
                "dass es seither keine nennenswerte Veränderung gab."
            ),
        },
        "LU_2.3": {
            "ziel": (
                "4.371.150 ha resultieren aus der Annahme einer gleichbleibenden Dauergrünlandfläche, wovon "
                "allerdings 333.050 ha mit der Hälfte des Zuwachses an Freiflächen-Solaranlagen belegt sind. "
                "Wenn organische Böden dafür vorgesehen werden, bietet sich diese Fläche zur Wiedervernässung als "
                "Beitrag zum Klimaschutz an.\n\n"
                "Der Ansatz erscheint aus Sicht der Ernährungssicherheit zukunftsfähig: Nach einer wissenschaftlichen "
                "Studie im Auftrag von Greenpeace würde zur Ernährung der Bevölkerung nach vollständiger Umstellung "
                "auf ökologische Wirtschaftsweise eine Dauergrünlandfläche von 4.300.000 ha ausreichen, selbst ohne "
                "Umstellung auf eine flächenschonende Ernährung.\n\n"
                "Ausgehend vom Jahr 1990 ist in Niedersachsen eine stetige Abnahme der Dauergrünlandnutzung von "
                "anfänglich 910.000 ha auf 691.600 ha zu verzeichnen. Der mit der Umwandlung ehemaliger Moorflächen "
                "in Ackerland verbundene Anstieg der Treibhausgasemissionen wird aus Klimaschutzgründen als nicht "
                "fortsetzbar angesehen; hier wird für Deutschland deshalb von einer gleichbleibenden Fläche ausgegangen."
            ),
        },
        "LU_3": {
            "ziel": (
                "Fortschreibung des Status quo in Übereinstimmung mit THGND. Die Bedeutung der Wälder für den "
                "Naturhaushalt und teilweise stark eingeschränkte anderweitige Nutzbarkeit sprechen gegen eine "
                "Verringerung der Waldflächen.\n\n"
                "\"Treibhausgasneutrales Deutschland 2050\": \"Die Aufforstung neuer Flächen konkurriert um "
                "anderweitige Flächennutzungsformen. Angesichts einer Abnahme der landwirtschaftlichen Nutzfläche "
                "bis 2050 um fast 1,5 Mio. ha wird davon ausgegangen, dass keine weiteren Flächen zur Aufforstung "
                "zur Verfügung stehen.\""
            ),
        },
        "LU_5": {
            "status": (
                "Bewertung der Studie von BWE, Fraunhofer IEE und Bosch zum Potenzial der Windenergie an Land in "
                "Deutschland: Nach Anwendung der Raumbewertung und der abgeleiteten Faktoren für die Nutzbarkeit "
                "ergibt sich ein bundesweites Flächenpotenzial von 20.890 km² beziehungsweise 5,8 % des "
                "Bundesgebiets.\n\n"
                "Die Analysen zum Potenzial der Windenergie in Deutschland erfolgen entlang einer Prozesskette. "
                "Im ersten Schritt werden die Flächen ermittelt, die aufgrund harter Tabukriterien und Restriktionen "
                "nicht für eine Windenergienutzung geeignet sind. Die verbleibenden Gebiete außerhalb dieser "
                "Ausschlussflächen werden im nächsten Schritt einer Raumbewertung unterzogen. Dabei wird abgewogen, "
                "welcher prozentuale Anteil der Flächen trotz festgestellter Nutzungskonflikte für die Windenergie "
                "nutzbar wäre."
            ),
            "ziel": (
                "Die Potenzialermittlung für die zur Aufstellung von Windenergieanlagen ohne Restriktionen nutzbaren "
                "Flächen auf Grundlage der Studie von BWE und Fraunhofer IWES wird übernommen, allerdings mit einem "
                "pauschalen Abschlag von 20 % zur Berücksichtigung nicht ausreichend einschätzbarer Veränderungen "
                "der räumlichen Gegebenheiten, zum Beispiel Ausweitung besiedelter Bereiche, Verkehrswege oder "
                "Schutzgebiete. Daraus resultiert ein Flächenpotenzial von 1.671.200 ha für Deutschland.\n\n"
                "Eine Sensitivitätsanalyse zeigt die große Bedeutung der Abstandsvorgaben: Eine Erhöhung des Puffers "
                "um 50 % würde die Potenzialfläche auf etwa ein Drittel reduzieren. Für die Berechnungen wurden "
                "Anlagen mit einer Gesamthöhe von 150 m beziehungsweise 208 m in Schwachwindgebieten zugrunde gelegt. "
                "Als Abstandsvorgabe zu Siedlungen, die den größten Einfluss auf die verbleibenden Flächen hat, wurden "
                "1.000 m angenommen."
            ),
        },
        "LU_6": {
            "status": (
                "172.556 ha Windparkfläche wurden von Onshore-Windenergieanlagen in Deutschland Mitte 2023 beansprucht. "
                "Das resultiert aus einer installierten Leistung von 59.502 MW und einer spezifischen Flächenbeanspruchung "
                "von 2,90 ha/MW.\n\n"
                "59.502 MW installierte Onshore-Windenergie-Leistung resultieren als Jahresdurchschnitt für Mitte 2023 "
                "unter der Annahme eines linear über das Jahr verteilten Zubaus: 61.016 MW betrug Ende 2023 die "
                "installierte Leistung der Onshore-Windenergie in Deutschland, Anfang 2023 waren es 57.988 MW."
            ),
            "ziel": (
                "715.191 ha Windparkfläche resultieren aus der Annahme, dass 2,0 % der Bodenfläche Deutschlands als "
                "Beitrag der Onshore-Windenergie zur Deckung des Strombedarfs genutzt werden. Mit einem Anteil von 43 % "
                "liegt dieser Ansatz weit unterhalb der Potenzialfläche.\n\n"
                "ACHTUNG! Nach Szenario-Modifikationen in S.1.34 kann der Zielwert dort von diesem Standardansatz "
                "abweichen.\n\n"
                "2.808.547 ha Erntefläche resultieren aus der bei 2 % Windparkfläche installierten Leistung von "
                "715.191 MW und einer durchschnittlichen spezifischen Erntefläche von 3,93 ha/MW.\n\n"
                "Die Anteile eingesetzter Standard-Referenzanlagen und Schwachwind-Referenzanlagen sind aus der Studie "
                "nicht ersichtlich. Bei der dort angewendeten flächenorientierten Platzierung ist davon auszugehen, "
                "dass mit der Standortauswahl für 2 % der Landesfläche das Potenzial der Standard-Referenzstandorte "
                "wohl kaum ausgeschöpft sein dürfte. Hier wird ein Standard-Referenzanlagen-Anteil von 100 % angenommen; "
                "daraus resultiert eine durchschnittliche spezifische Erntefläche von 3,93 ha/MW.\n\n"
                "3,93 ha/MW spezifische Erntefläche der Standard-Referenzanlage mit 3 MW Nennleistung, 100 m Nabenhöhe "
                "und 100 m Rotordurchmesser: Aus 7.854 m² Rotorfläche resultiert bei Zugrundelegung des üblichen "
                "Mindestabstands zu Nachbaranlagen von 5 Rotordurchmessern in Hauptwindrichtung und 3 Rotordurchmessern "
                "rechtwinklig dazu 11,8 ha Anlagen-Erntefläche. In Bezug zur Nennleistung ergibt sich 3,93 ha/MW "
                "spezifische Erntefläche."
            ),
        },
    }

    replacement = row_specific.get(row_code)
    if replacement:
        if "status" in replacement:
            note_parts["status_information"] = replacement["status"]
        if "ziel" in replacement:
            note_parts["ziel_information"] = replacement["ziel"]
        if "general" in replacement:
            note_parts["general_information"] = replacement["general"]

    return note_parts


def _clean_landuse_source(ref: dict) -> dict:
    cleaned = dict(ref)
    label = html.unescape((cleaned.get("label") or "").strip())
    description = html.unescape((cleaned.get("description") or "").strip())
    url = (cleaned.get("url") or "").strip()
    title_match = re.search(r'"([^"]+)"', description)
    title = title_match.group(1).strip() if title_match else ""

    label_map = {
        "33111-01-02-4": "GENESIS",
        "41121-0102.1 R": "DESTATIS",
        "Solarthermie Kollektorfläche": "Solarthermie-Kollektorfläche",
        "PV-Leistung gesamt\nPV-Leistung Freifl.Anl.": "PV-Leistung gesamt / PV-Leistung Freifl.-Anlagen",
        "Seite 9": "Photovoltaik auf Freiflächen – Leitfaden",
        "Stelllungnahme zum \n1.Runden Tisch \nNr. 20, S. 5": "Stellungnahme zum 1. Runden Tisch Nr. 20, S. 5",
        ", S. 4": "Flächenverfügbarkeit und Flächenbedarfe, S. 4",
    }
    if label in label_map:
        cleaned["label"] = label_map[label]
    elif not label and title:
        cleaned["label"] = title
    elif label.startswith("S.") and title:
        cleaned["label"] = f"{title} ({label})"
    elif label.startswith("Tab.") and title:
        cleaned["label"] = f"{title} ({label})"
    elif url and not label:
        cleaned["label"] = url.rstrip("/").split("/")[-1]
    else:
        cleaned["label"] = label
    cleaned["description"] = description
    cleaned["url"] = url
    return cleaned


def _source_base_name(description: str, url: str) -> str:
    description = (description or "").strip()
    if description:
        title_match = re.search(r'"([^"]+)"', description)
        if title_match:
            return title_match.group(1).strip()
        if ":" in description:
            return description.split(":", 1)[0].strip()
        return description[:80].strip()
    if url:
        return url.rstrip("/").split("/")[-1]
    return "Quelle"


def _clean_renewable_source(ref: dict) -> dict:
    cleaned = dict(ref)
    label = html.unescape((cleaned.get("label") or "").strip())
    description = html.unescape((cleaned.get("description") or "").strip())
    url = (cleaned.get("url") or "").strip()

    label = re.sub(r"\s+", " ", label).strip()
    label = label.lstrip(",").strip()
    description = re.sub(r"\s+", " ", description).strip()
    base_name = _source_base_name(description, url)

    pageish_label = (
        not label
        or label.startswith("S.")
        or label.startswith("Tab.")
        or label.startswith("Abs.")
        or label.startswith("Anhang")
        or label.startswith("Status Quo")
        or label.startswith("Potenziale")
        or label.startswith("Ho")
        or label.startswith(",")
    )

    if pageish_label:
        cleaned["label"] = f"{base_name} ({label})" if label else base_name
    else:
        cleaned["label"] = label

    cleaned["description"] = description
    cleaned["url"] = url
    return cleaned


def _clean_renewable_note_parts(
    row_code: str,
    note_parts: dict[str, str],
    source_refs: list[dict],
) -> tuple[dict[str, str], list[dict]]:
    note_parts = {
        "general_information": _normalize_text_fragment(note_parts.get("general_information", "")),
        "status_information": _normalize_text_fragment(note_parts.get("status_information", "")),
        "ziel_information": _normalize_text_fragment(note_parts.get("ziel_information", "")),
    }

    replacements = {
        "4.1.2.1": {
            "status": (
                "Gemäß einer Studie des Von-Thünen-Instituts waren in Deutschland im Jahr 2022 11.200 ha "
                "Ackerfläche mit Kurzumtriebsplantagen einschließlich Miscanthus belegt. Hier wird konservativ "
                "davon ausgegangen, dass es seither keine nennenswerte Veränderung gab."
            ),
            "ziel": (
                "Kein weiterer Ausbau, Beibehaltung des Status. Die Erträge liegen bei Verwendung trockener "
                "Brennstoffe zwar in derselben Größenordnung wie bei Biogas. Dieses Potenzial erscheint jedoch "
                "besser zur Substitution im besonders kritischen Kraftstoffbereich geeignet und wird daher "
                "bevorzugt."
            ),
            "sources": [],
        },
        "4.1.2.1.1": {
            "status": (
                "29,9 MWh/ha/a, wobei dieser Wert für Kurzumtriebsplantagen im Ergebnis auch auf Miscanthus "
                "übertragen werden kann. Die in den zugrunde gelegten Quellen verwendeten Kennwerte für den "
                "Bruttojahresbrennstoffertrag erscheinen in der jüngeren FNR-Publikation unverändert.\n\n"
                "Typische Erträge von Kurzumtriebsplantagen wie Pappel oder Weide liegen bei 12 t/ha/a "
                "Masseertrag beziehungsweise 185 GJ/ha/a Energieertrag, entsprechend 51,4 MWh/ha/a bei einem "
                "Wassergehalt von 15 %. Da die Verfeuerung meist mit deutlich höherem Wassergehalt erfolgt, "
                "reduziert sich der nutzbare Heizwert auf rund 58,1 % und damit auf 29,9 MWh/ha/a."
            ),
            "ziel": (
                "51,4 MWh/ha/a. Im Unterschied zum Status wird hier von luftgetrockneten Brennstoffen mit "
                "15 % Wassergehalt ausgegangen, um die Verschwendung eines Teils der enthaltenen Energie zu "
                "vermeiden. Eventuelle Einflüsse auf die Wachstumsbedingungen, beispielsweise durch den "
                "Klimawandel, sind aus heutiger Sicht nicht belastbar einschätzbar."
            ),
            "sources": [],
        },
        "4.1.2.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Status-Anbaufläche und dem Status-Energieertrag "
                "von Energieholz aus Ackerbau."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Anbaufläche und dem Ziel-Energieertrag "
                "von Energieholz aus Ackerbau."
            ),
            "sources": [],
        },
        "4.1.3": {
            "status": (
                "Der Statuswert ergibt sich aus der Summe des Energieholzaufkommens aus Forstwirtschaft "
                "und aus Ackerbau."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Summe des Ziel-Aufkommens aus Forstwirtschaft "
                "und aus Ackerbau."
            ),
            "sources": [],
        },
        "4.1.3.4": {
            "status": (
                "0 %. Da der Energieholzeinsatz für eingespeiste KWK-Abwärme bereits über den Einsatz "
                "für Stromerzeugung in die Kalkulation eingeht, wird hier nur der Einsatz reiner "
                "Holz-Heizwerke ohne Stromerzeugung betrachtet. Für Deutschland liegen dazu keine "
                "geeigneten getrennten Statistikangaben vor, weshalb dieser Beitrag hier vernachlässigt wird."
            ),
            "ziel": (
                "Reine Biomasse-Heizwerke zur Versorgung mit Gebäudewärme über Wärmenetze erscheinen "
                "für die Zukunft nicht sinnvoll. Vorrangig genutzt werden soll der begrenzte "
                "Brennstoffanfall für anspruchsvollere Anwendungsbereiche wie Prozesswärme oder "
                "Stromerzeugung."
            ),
            "sources": [],
        },
        "4.3.1": {
            "status": (
                "Der Statuswert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Status-Anteilen für Gebäudewärme bei Energieholz und Stroh."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Ziel-Anteilen für Gebäudewärme bei Energieholz und Stroh."
            ),
            "sources": [],
        },
        "4.3.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Status-Anteilen für Prozesswärme bei Energieholz und Stroh."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Ziel-Anteilen für Prozesswärme bei Energieholz und Stroh."
            ),
            "sources": [],
        },
        "4.3.3": {
            "status": (
                "Der Statuswert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Status-Anteilen für Verstromung bei Energieholz und Stroh."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem gesamten festen NAWARO-Brennstoffaufkommen und den "
                "Ziel-Anteilen für Verstromung bei Energieholz und Stroh."
            ),
            "sources": [],
        },
        "4.3.3.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem festen NAWARO-Brennstoffaufkommen für Verstromung "
                "und dem Status-Nutzungsgrad des Kraftwerks."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem festen NAWARO-Brennstoffaufkommen für Verstromung "
                "und dem Ziel-Nutzungsgrad des Kraftwerks."
            ),
            "sources": [],
        },
        "4.3.3.1": {
            "status": (
                "Annahme von 25 % elektrischem Wirkungsgrad, orientiert an der jüngeren der beiden "
                "recherchierten Anlagen. Für Neubau-Anlagen werden zwar 30 % bis 35 % angegeben, "
                "dies bleibt hier aber mit Blick auf den heutigen Anlagenbestand unberücksichtigt."
            ),
            "ziel": (
                "35 % elektrischer Wirkungsgrad entsprechend dem oberen Bereich heutiger Neuanlagen. "
                "Wesentliche zusätzliche Wirkungsgradsteigerungen der Dampfturbinentechnik werden "
                "nicht erwartet."
            ),
            "sources": [],
        },
        "4.3.3.3": {
            "status": (
                "In Anlehnung an die betrachtete Referenzanlage wird ein effektiver Nutzungsgrad der "
                "verwerteten KWK-Abwärme von 45 % angenommen."
            ),
            "ziel": (
                "35 % thermischer Wirkungsgrad gemäß der Referenzanlage dienen hier als Zielwert des "
                "künftigen Anlagenparks. Wesentliche Steigerungen der Dampfturbinentechnik werden "
                "nicht erwartet."
            ),
            "sources": [],
        },
        "4.3.3.4": {
            "status": (
                "Der Statuswert ergibt sich aus dem festen NAWARO-Brennstoffaufkommen für Verstromung "
                "und dem Status-Nutzungsgrad der wirksam genutzten KWK-Abwärme."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem festen NAWARO-Brennstoffaufkommen für Verstromung "
                "und dem Ziel-Nutzungsgrad der wirksam genutzten KWK-Abwärme."
            ),
            "sources": [],
        },
        "4.3.4.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem Brennstoffeinsatz für Heizwerke und Wärmenetze "
                "und dem Status-Nutzungsgrad des Wärmenetzpfads."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Brennstoffeinsatz für Heizwerke und Wärmenetze "
                "und dem Ziel-Nutzungsgrad des Wärmenetzpfads."
            ),
            "sources": [],
        },
        "4.4.1": {
            "status": "4.525 GWh Nettostromerzeugung aus dem biogenen Anteil fester Abfälle im Jahr 2023 gemäß BMWK.",
            "ziel": (
                "Beibehaltung des Statuswertes aufgrund einer aus heutiger Sicht schwer einschätzbaren "
                "Entwicklung. Einerseits ließe sich der Anteil energetischer Verwertung vermutlich noch "
                "erhöhen. Andererseits könnte die weitere Optimierung der Müllvermeidung die energetisch "
                "verwertbaren Mengen senken."
            ),
        },
        "4.4.2": {
            "status": "9.913 GWh Wärme-Endenergie aus dem biogenen Anteil fester Abfälle im Jahr 2023 gemäß BMWK.",
            "ziel": (
                "Beibehaltung des Statuswertes aufgrund einer aus heutiger Sicht schwer einschätzbaren "
                "Entwicklung. Einerseits ließe sich der Anteil energetischer Verwertung vermutlich noch "
                "erhöhen. Andererseits könnte die weitere Optimierung der Müllvermeidung die energetisch "
                "verwertbaren Mengen senken."
            ),
        },
        "5.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Status-Anbaufläche für Biogas-Energiepflanzen "
                "und dem Status-Methanertrag."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Anbaufläche für Biogas-Energiepflanzen "
                "und dem Ziel-Methanertrag."
            ),
            "sources": [],
        },
        "5.2": {
            "status": (
                "15.998 GWh Heizwert der Biogasmenge aus Rest- und Abfallstoffen, exklusive Deponie- "
                "und Kläranlagen, resultieren aus einer Gesamtmenge von 74 PJ entsprechend 20.556 GWh "
                "im Jahr 2019 abzüglich 4.558 GWh aus Deponien und Kläranlagen."
            ),
            "ziel": (
                "44.571 GWh resultieren aus der konservativen Annahme, dass sich 80 % des unteren "
                "Potenzialwertes von 258 PJ für Rest- und Abfallstoffe tatsächlich sinnvoll realisieren "
                "lassen, exklusive der separat erfassten Gase aus Deponien und Kläranlagen."
            ),
        },
        "5.3": {
            "status": (
                "Einen Heizwert von 4.558 GWh besaß die im Jahr 2022 praktisch vollständig verstromte "
                "Gasmenge aus Deponien und Kläranlagen. Der Wert ergibt sich aus der Stromerzeugung "
                "und einem durchschnittlichen Verstromungswirkungsgrad von 38 %."
            ),
            "ziel": (
                "12.762 GWh resultieren aus der Annahme, dass sich diese Biogasmenge genauso auf das "
                "2,8-Fache steigern lässt wie die Biogasmengen aus Rest- und Abfallstoffen insgesamt."
            ),
            "sources": [],
        },
        "5.4.2": {
            "status": (
                "Lediglich 25 % des 2022 zu Biomethan aufbereiteten Biogases wurden nicht verstromt, "
                "sondern als Kraftstoff oder Wärme genutzt oder exportiert. Bezogen auf die gesamte "
                "Biogaserzeugung wurden damit rund 96 % verstromt."
            ),
            "ziel": (
                "Auf die Verstromung von Biogas wird zugunsten der mobilen Anwendungen verzichtet. "
                "Mit dem begrenzten Brennstoffangebot könnte nur ein geringer Beitrag zur Stromversorgung "
                "geleistet werden. Für die Substitution fossiler Kraftstoffe und für Prozesswärme ist "
                "Biogas deutlich wertvoller."
            ),
            "sources": [],
        },
        "5.4.2.1": {
            "status": "Aktueller Durchschnittswert des deutschen Anlagenbestandes im Jahr 2022 gemäß FNR.",
            "ziel": (
                "Orientiert am oberen Ende der heutigen Bandbreite elektrischer Wirkungsgrade von "
                "Biogas-BHKW zwischen 28 % und 47 %."
            ),
            "sources": [],
        },
        "5.4.2.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem Status-Anteil des Biogases für Verstromung "
                "und dem Status-Nutzungsgrad der Biogasverstromung."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Ziel-Anteil des Biogases für Verstromung "
                "und dem Ziel-Nutzungsgrad der Biogasverstromung."
            ),
            "sources": [],
        },
        "5.4.2.3": {
            "status": (
                "Mit 18.372 GWh ist die Wärmebereitstellung aus Biogas und Biomethan im Jahr 2022 "
                "angegeben. Für die tatsächlich über das Jahr nutzbare Wärmeverwertung ergibt sich "
                "ein Nutzungsgrad von 21,9 % aus dem Verhältnis zur gesamten Biogas- und Biomethanmenge."
            ),
            "ziel": (
                "Leichte Erhöhung gegenüber dem Status. Beispielsweise kann eine stärkere Nutzung von "
                "Satelliten-BHKW an Orten mit Wärmeabnahme die Abwärmenutzung steigern. Gleichzeitig "
                "würde bei stärker intermittierendem BHKW-Betrieb zur Stromsystemstützung die zeitliche "
                "Übereinstimmung von Wärmeangebot und Wärmebedarf schwieriger."
            ),
        },
        "5.4.3": {
            "status": "1,2 % der gesamten Biogaserzeugung in Deutschland wurden 2022 im Verkehrssektor als Kraftstoff verwendet.",
            "ziel": (
                "Biogas ist vorrangig zur Kraftstofferzeugung für die mobilen Anwendungen an Land und "
                "auf See vorgesehen, die sich nicht sinnvoll elektrifizieren lassen, insbesondere im "
                "Güterverkehr."
            ),
        },
        "5.4.3.1": {
            "status": (
                "Ein Wandlungsnutzungsgrad von 98 % für den Pfad Biogas zu Biomethan resultiert aus "
                "dem Strombedarf der Aufbereitung und dem Energieinhalt des erzeugten Biomethans."
            ),
            "ziel": (
                "Wegen der verlustarmen Bereitstellung von hochkomprimiertem Biomethan wird dieser "
                "Pfad für mobile Anwendungen am Boden vorgesehen. Der heutige Nutzungsgrad wird auch "
                "für die Zukunft angenommen."
            ),
        },
        "5.4.3.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem Status-Anteil des Biogases für mobile Anwendungen "
                "als Biomethan und dem Status-Nutzungsgrad der Kraftstoffbereitstellung."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Ziel-Anteil des Biogases für mobile Anwendungen "
                "als Biomethan und dem Ziel-Nutzungsgrad der Kraftstoffbereitstellung."
            ),
            "sources": [],
        },
        "5.4.4.2": {
            "status": (
                "Der Statuswert ist null, weil derzeit keine Flüssigkraftstoffe aus Biogas hergestellt werden."
            ),
            "ziel": (
                "Der Zielwert ist null, weil in diesem Szenario bewusst auf Flüssigkraftstoffe aus Biogas "
                "verzichtet wird."
            ),
            "sources": [],
        },
        "6.1.1": {
            "status": (
                "Gemäß FNR lag die Anbaufläche für Biodiesel im Jahr 2022 bei 665.000 ha. Das entspricht "
                "25,6 % der gesamten Energiepflanzen-Anbaufläche, 5,7 % der Ackerfläche beziehungsweise "
                "3,7 % der Landwirtschaftsfläche. Mit dem resultierenden Biodiesel von rund 11.804 GWh/a "
                "lassen sich etwa zwei Drittel des Dieselbedarfs der deutschen Landwirtschaft decken."
            ),
            "ziel": (
                "Innerhalb der Extrempositionen beim Anbau energetisch genutzter nachwachsender Rohstoffe "
                "geht der gewählte Ansatz von einer Halbierung der Pflanzenöl-Anbaufläche aus. Die "
                "Zielfläche von 303.000 ha entspricht 1,7 % der Landwirtschaftsfläche. Die Minderung "
                "erfolgt zugunsten von Biogas wegen der deutlich höheren Energieerträge."
            ),
        },
        "6.1.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Status-Anbaufläche für Biodiesel und dem "
                "Status-Energieertrag des Anbaus."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Anbaufläche für Biodiesel und dem "
                "Ziel-Energieertrag des Anbaus."
            ),
            "sources": [],
        },
        "6.1.2": {
            "status": (
                "Ein Biodiesel-Import von 13.403 GWh resultiert aus dem in Deutschland 2022 verursachten "
                "Biodiesel- und Pflanzenölverbrauch, überwiegend als Beimischung zum Dieselkraftstoff, "
                "abzüglich der auf eigener Fläche erzeugten Menge. Der Importanteil liegt damit bei "
                "53,2 % des Verbrauchs."
            ),
            "ziel": (
                "Ein Import von Pflanzenölprodukten für energetische Zwecke ist nicht vorgesehen. "
                "Vor dem Hintergrund globaler Flächenkonkurrenzen, Waldverlusten und sozialer Probleme "
                "erscheint die Inanspruchnahme von Anbauflächen im Ausland nicht sinnvoll."
            ),
        },
        "6.1.3": {
            "status": (
                "Der Statuswert ergibt sich aus der in Deutschland erzeugten Biodieselmenge "
                "plus dem Nettoimport."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Zielmenge aus heimischem Anbau; ein Import ist "
                "im Zielbild nicht vorgesehen."
            ),
            "sources": [],
        },
        "6.1.3.1.1": {
            "status": (
                "Der Statuswert ergibt sich aus dem gesamten Biodieselaufkommen und dem Status-Anteil "
                "für mobile Anwendungen."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem gesamten Biodieselaufkommen und dem Ziel-Anteil "
                "für mobile Anwendungen."
            ),
            "sources": [],
        },
        "6.1.3.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem Verhältnis des Biodiesel- und Pflanzenölverbrauchs "
                "für Verstromung von 233 GWh zum Gesamtverbrauch von 25.206 GWh im Jahr 2022."
            ),
            "ziel": (
                "Auf die Verstromung von Biodiesel beziehungsweise Pflanzenöl wird zugunsten der mobilen "
                "Anwendungen verzichtet, da mit dem begrenzten Brennstoffangebot nur ein vernachlässigbar "
                "kleiner Beitrag zur Stromversorgung geleistet werden könnte."
            ),
        },
        "6.1.3.2.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem für Verstromung eingesetzten Biodiesel und dem "
                "Status-Nutzungsgrad des Blockheizkraftwerks."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Ziel-Anteil für Verstromung und dem Ziel-Nutzungsgrad "
                "des Blockheizkraftwerks."
            ),
            "sources": [],
        },
        "6.1.3.2.3": {
            "status": (
                "Repräsentative Statistikdaten zum thermischen Jahresnutzungsgrad des tatsächlich als "
                "Gebäudewärme verwerteten Abwärmeanteils liegen nicht vor. Da die Anlagen meist stromgeführt "
                "betrieben werden, dürfte der effektiv nutzbare Wärmeanteil deutlich unter dem thermischen "
                "BHKW-Wirkungsgrad liegen. Hier wird deshalb eine optimistische Annahme getroffen."
            ),
            "ziel": (
                "Es ist davon auszugehen, dass bei der heutigen Blockheizkraftwerk-Technologie die "
                "Effizienzpotenziale weitgehend ausgeschöpft sind. Daher wird der Statuswert als Ziel "
                "übernommen."
            ),
            "sources": [],
        },
        "6.2.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Status-Anbaufläche für Bioethanol und dem "
                "Status-Energieertrag des Anbaus."
            ),
            "ziel": (
                "Der Zielwert ist null, weil im Zielbild keine Energiepflanzenflächen mehr für "
                "Bioethanol vorgesehen sind."
            ),
            "sources": [],
        },
        "6.2.2": {
            "status": (
                "Ein Bioethanol-Import von 4.991 GWh resultiert aus dem in Deutschland 2022 verursachten "
                "Bioethanolverbrauch als Beimischung zum Ottokraftstoff abzüglich der auf eigener Fläche "
                "erzeugten Menge. Der Importanteil wird auf 57,4 % des Verbrauchs geschätzt."
            ),
            "ziel": (
                "Ein Import von Bioethanol oder dessen Ausgangsprodukten für energetische Zwecke ist "
                "nicht mehr vorgesehen. Vor dem Hintergrund globaler Flächenkonkurrenzen erscheint die "
                "Inanspruchnahme von Anbauflächen im Ausland nicht sinnvoll."
            ),
        },
        "7.1": {
            "status": (
                "Der jährliche Stromverbrauch der Wärmepumpen in Deutschland lag 2023 bei insgesamt "
                "10.108 GWh. Darin enthalten sind Luft-Wasser-Wärmepumpen, Sole-/Wasser-Wärmepumpen "
                "sowie zusätzlich 354 GWh für Brauchwasserwärmepumpen."
            ),
            "ziel": (
                "Der Zielwert wird aus dem verbleibenden Bedarf an Gebäudewärme abgeleitet, der nicht "
                "durch andere Wärmequellen gedeckt wird. Wärmepumpen werden hier als bevorzugte Lösung "
                "angenommen, um Brennstoffpotenziale zu schonen und elektrische Widerstandsheizungen "
                "zu ersetzen. Unter Annahme von 1.700 Jahresvollbenutzungsstunden ergibt sich eine "
                "erforderliche elektrische Anschlussleistung von rund 71.630 MW."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
                {
                    "section": "ziel",
                    "label": "Bundesverband Wärmepumpe",
                    "description": (
                        "BUNDESVERBAND WÄRMEPUMPE e. V. (2014) Online-Portal: "
                        "\"Immer mehr Bauherren setzen auf Wärmepumpen\". Online am 02.04.2025 "
                        "nicht mehr verfügbar."
                    ),
                    "url": "http://www.waermepumpe.de/presse/pressemitteilungen/pressemitteilung/article/immer-mehr-bauherren-setzen-auf-waermepumpe.html",
                },
            ],
        },
        "7.1.1": {
            "status": (
                "An der gesamten Stromaufnahme der Wärmepumpen hatten Luft-Wasser-Wärmepumpen im Jahr "
                "2023 einen Anteil von 71,2 %. Der Wert ergibt sich aus den statistischen Einzelwerten "
                "für Luft- sowie Erdreich-/Wasser-Wärmepumpen."
            ),
            "ziel": (
                "Langfristig wird ein Anteil von 92,2 % Luftwärmepumpen angenommen. Grundlage ist das "
                "Verhältnis der Absatzzahlen von 356.000 Luftwärmepumpen zu 30.000 Erd- bzw. "
                "wassergekoppelten Anlagen, das hier vereinfacht auch für den künftigen Bestand "
                "unterstellt wird."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
                {
                    "section": "ziel",
                    "label": "Bundesverband Wärmepumpe",
                    "description": (
                        "BUNDESVERBAND WÄRMEPUMPE e. V. (2025) Online-Portal: "
                        "\"Wärmepumpenabsatz 2023 & Wärmepumpenabsatz 2022\". Jüngster Zugriff am "
                        "24.03.2025."
                    ),
                    "url": "https://www.waermepumpe.de/presse/zahlen-daten/absatzzahlen/",
                },
            ],
        },
        "7.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der gesamten Stromaufnahme der Wärmepumpen und dem "
                "Status-Anteil der Anlagen mit Luftkopplung."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Stromaufnahme der Wärmepumpen und dem "
                "angenommenen Ziel-Anteil der Luftwärmepumpen."
            ),
            "sources": [],
        },
        "7.1.2.1": {
            "general": (
                "Die Jahresarbeitszahl einer Wärmepumpen-Anlage gibt an, wie vielfach die eingesetzte "
                "Antriebsenergie als Nutzwärme bereitgestellt wird. Die Differenz zur eingesetzten "
                "Antriebsenergie stammt aus der aufgenommenen Umgebungswärme."
            ),
            "status": (
                "Die Luft-Wasser-Wärmepumpen im deutschen Bestand arbeiteten 2023 mit einer "
                "durchschnittlichen Jahresarbeitszahl von 3,2. Dieser Wert ist aus den statistischen "
                "Bestandsdaten abgeleitet und steht im Einklang mit aktuellen Feldtest-Ergebnissen."
            ),
            "ziel": (
                "Als Zielwert werden 4,2 angesetzt. Das wird in Anlehnung an veröffentlichte "
                "Forschungsergebnisse als konservativ erreichbar bewertet. Höhere Branchenangaben "
                "werden hier bewusst nicht übernommen."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "Fraunhofer ISE",
                    "description": (
                        "FRAUNHOFER ISE (2024) \"Wärmepumpenfeldtest: Zwischenergebnisse bestätigen "
                        "effizienten Betrieb auch im Altbau\". Jüngster Zugriff am 24.03.2025."
                    ),
                    "url": "https://www.ise.fraunhofer.de/de/presse-und-medien/news/2024/waermepumpenfeldstest-zwischenergebnisse-bestaetigen-effizienten-betrieb-auch-im-altbau.html",
                },
                {
                    "section": "ziel",
                    "label": "TGA+E Fachplaner",
                    "description": (
                        "TGA+E FACHPLANER, Online-Auftritt (18.05.2021): "
                        "\"Wärmepumpen: Jahresarbeitszahl von 9,1 bis 2050 möglich\". Jüngster Zugriff "
                        "am 24.03.2025."
                    ),
                    "url": "https://www.tga-fachplaner.de/node/165492/print",
                },
            ],
        },
        "7.1.2.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Stromaufnahme luftgekoppelter Wärmepumpen und ihrer "
                "Status-Jahresarbeitszahl."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Stromaufnahme luftgekoppelter Wärmepumpen und "
                "der angenommenen Ziel-Jahresarbeitszahl."
            ),
            "sources": [],
        },
        "7.1.2.3": {
            "status": (
                "Der Statuswert ergibt sich aus der bereitgestellten Nutzwärme der Luftwärmepumpen "
                "abzüglich ihrer eingesetzten Antriebsenergie."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Nutzwärme der Luftwärmepumpen abzüglich ihrer "
                "elektrischen Antriebsenergie."
            ),
            "sources": [],
        },
        "7.1.3": {
            "status": (
                "Der Statuswert ist der verbleibende Anteil der Erdreich- und wassergekoppelten "
                "Wärmepumpen an der gesamten Stromaufnahme und entspricht dem Gegenstück zum "
                "Luftwärmepumpen-Anteil."
            ),
            "ziel": (
                "Der Zielwert ist der komplementäre Restanteil zu den angenommenen 92,2 % "
                "Luftwärmepumpen und beträgt damit 7,8 %."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
                {
                    "section": "ziel",
                    "label": "Bundesverband Wärmepumpe",
                    "description": (
                        "BUNDESVERBAND WÄRMEPUMPE e. V. (2025) Online-Portal: "
                        "\"Wärmepumpenabsatz 2023 & Wärmepumpenabsatz 2022\". Jüngster Zugriff am "
                        "24.03.2025."
                    ),
                    "url": "https://www.waermepumpe.de/presse/zahlen-daten/absatzzahlen/",
                },
            ],
        },
        "7.1.4": {
            "status": (
                "Der Statuswert ergibt sich aus der gesamten Stromaufnahme der Wärmepumpen und dem "
                "Status-Anteil der Erdreich- und wassergekoppelten Anlagen."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Stromaufnahme der Wärmepumpen und dem "
                "verbleibenden Ziel-Anteil der Erdreich- und wassergekoppelten Anlagen."
            ),
            "sources": [],
        },
        "7.1.4.1": {
            "general": (
                "Die Jahresarbeitszahl gibt an, wie vielfach die eingesetzte Antriebsenergie als "
                "Nutzwärme bereitgestellt wird. Die zusätzliche Wärme stammt hier aus dem Erdreich "
                "oder dem Grundwasser."
            ),
            "status": (
                "Die Sole-Wasser- und Wasser-Wasser-Wärmepumpen im deutschen Bestand arbeiteten 2023 "
                "mit einer durchschnittlichen Jahresarbeitszahl von 3,8. Der Wert ist aus den "
                "statistischen Bestandsdaten abgeleitet."
            ),
            "ziel": (
                "Als Zielwert werden 4,9 angesetzt. Mangels belastbarer Langfristdaten wird vereinfacht "
                "unterstellt, dass sich die Effizienz im selben Verhältnis verbessert wie bei den "
                "luftgekoppelten Wärmepumpen."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
                {
                    "section": "ziel",
                    "label": "TGA+E Fachplaner",
                    "description": (
                        "TGA+E FACHPLANER, Online-Auftritt (18.05.2021): "
                        "\"Wärmepumpen: Jahresarbeitszahl von 9,1 bis 2050 möglich\". Jüngster Zugriff "
                        "am 24.03.2025."
                    ),
                    "url": "https://www.tga-fachplaner.de/node/165492/print",
                },
            ],
        },
        "7.1.4.2": {
            "status": (
                "Der Statuswert ergibt sich aus der Stromaufnahme der Erdreich-/Wasser-Wärmepumpen "
                "und ihrer Status-Jahresarbeitszahl."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Stromaufnahme der Erdreich-/Wasser-Wärmepumpen "
                "und der angenommenen Ziel-Jahresarbeitszahl."
            ),
            "sources": [],
        },
        "7.1.4.3": {
            "status": (
                "Der Statuswert ergibt sich aus der bereitgestellten Nutzwärme der Erdreich- und "
                "wassergekoppelten Wärmepumpen abzüglich ihrer elektrischen Antriebsenergie."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Ziel-Nutzwärme der Erdreich- und "
                "wassergekoppelten Wärmepumpen abzüglich ihrer elektrischen Antriebsenergie."
            ),
            "sources": [],
        },
        "7.1.4.3.1": {
            "status": (
                "Für erdreichgekoppelte Wärmepumpenanlagen wird ein durchschnittliches "
                "Wärmeentzugspotenzial von 1.000 MWh je Hektar und Jahr angesetzt. Dieser Wert dient "
                "zur Abschätzung der für den Wärmeentzug beanspruchten Fläche und zur Vermeidung von "
                "Überbeanspruchungen."
            ),
            "ziel": (
                "Der Statuswert wird übernommen, da der Wärmeertrag von der Bodenbeschaffenheit abhängt "
                "und diese als langfristig konstant angenommen wird."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "Kaltschmitt/Streicher/Wiese",
                    "description": (
                        "KALTSCHMITT M., STREICHER W., WIESE A. (2006): "
                        "\"Erneuerbare Energien. Systemtechnik, Wirtschaftlichkeit, Umweltaspekte\"."
                    ),
                    "url": "",
                },
            ],
        },
        "7.1.4.3.2": {
            "status": (
                "Der Statuswert ergibt sich aus dem Status-Wärmegewinn aus Erdreich bzw. Grundwasser "
                "und dem angesetzten spezifischen Wärmeertrag je Hektar."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Ziel-Wärmegewinn aus Erdreich bzw. Grundwasser und "
                "dem unveränderten spezifischen Wärmeertrag je Hektar."
            ),
            "sources": [],
        },
        "7.1.4.3.3": {
            "status": (
                "Der Statuswert entspricht der Siedlungsfläche aus dem Flächennutzungsmodell und dient "
                "hier als Bezugsfläche für den beanspruchten Anteil."
            ),
            "ziel": (
                "Der Zielwert entspricht der Ziel-Siedlungsfläche aus dem Flächennutzungsmodell und "
                "dient hier als Bezugsfläche für den beanspruchten Anteil."
            ),
            "sources": [],
        },
        "7.1.4.3.4": {
            "status": (
                "Der Statuswert ergibt sich aus dem Verhältnis der beanspruchten Entzugsfläche zur "
                "gesamten Siedlungsfläche im Status."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem Verhältnis der beanspruchten Entzugsfläche zur "
                "gesamten Siedlungsfläche im Ziel."
            ),
            "sources": [],
        },
        "8.1": {
            "status": (
                "Gemäß BMWK lag die installierte elektrische Leistung der Tiefengeothermie in Deutschland "
                "im Jahr 2023 bei 57 MW."
            ),
            "ziel": (
                "Als Zielwert wird null angesetzt. Hintergrund ist die Einschätzung, dass unter den "
                "gegebenen Randbedingungen keine nennenswerte Netto-Stromerzeugung aus Tiefengeothermie "
                "zu erwarten ist."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
            ],
        },
        "8.1.1": {
            "status": (
                "3.421 Vollbetriebsstunden pro Jahr ergeben sich aus einer Stromerzeugung von 195 GWh "
                "und einer installierten Leistung von 57 MW im Jahr 2023."
            ),
            "ziel": (
                "Unter den gegebenen Randbedingungen wird keine nennenswerte Veränderung der "
                "Vollbetriebsstunden angenommen."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
            ],
        },
        "8.1.2": {
            "status": (
                "Der Statuswert ergibt sich aus der installierten elektrischen Leistung der "
                "Tiefengeothermie und den Status-Vollbetriebsstunden."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der angenommenen Netzeinspeisung von null und bleibt "
                "deshalb ebenfalls null."
            ),
            "sources": [],
        },
        "8.2": {
            "status": (
                "Die Bereitstellung von Gebäudewärme aus Tiefengeothermie lag 2023 in Deutschland bei "
                "1.797 GWh."
            ),
            "ziel": (
                "Für das Zieljahr werden 12.000 GWh angenommen. Zwar gehen Studien zu einer "
                "treibhausgasneutralen Wärmeversorgung von deutlich höheren technischen Potenzialen aus, "
                "hier wird jedoch aus Nachhaltigkeitsgründen nur ein deutlich reduzierter Wert angesetzt. "
                "Als erneuerbare Wärme kann nur die Energiemenge entnommen werden, die im selben Zeitraum "
                "wieder in das geothermische Betrachtungsvolumen zufließt."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "BMWK",
                    "description": (
                        "Bundesministerium für Wirtschaft und Klimaschutz - Daten der AGEE-Statistik: "
                        "Zeitreihen zur Entwicklung der erneuerbaren Energien in Deutschland. Stand "
                        "September 2024. Jüngster Zugriff am 29.01.2025."
                    ),
                    "url": "https://www.bmwk.de/Redaktion/DE/Dossier/erneuerbare-energien#entwicklung-in-zahlen",
                },
                {
                    "section": "ziel",
                    "label": "LIAG Metastudie",
                    "description": (
                        "Leibnitz-Institut für angewandte Geophysik Hannover (30.05.2022). "
                        "\"Metastudie zur nationalen Erdwärmestrategie - Ersatz fossiler Brennstoffe im "
                        "Bereich Raumwärme und Warmwasser durch Geothermie als unverzichtbarer Bestandteil "
                        "im Energiesektor Ökowärme bis 2045\". Jüngster Zugriff 08.02.2025."
                    ),
                    "url": "https://www.geothermie.de/fileadmin/user_upload/Downloads/Metastudie_Geothermie__LIAG_2022_.pdf",
                },
                {
                    "section": "ziel",
                    "label": "Bundesverband Geothermie",
                    "description": (
                        "Bundesverband Geothermie, Internetauftritt. "
                        "\"Potenzial, geothermisches - Tiefe Geothermie\". Jüngster Zugriff 08.02.2025."
                    ),
                    "url": "https://www.geothermie.de/bibliothek/lexikon-der-geothermie/p/potenzial-geothermisches-tiefe-geothermie",
                },
            ],
        },
        "9.1": {
            "status": (
                "Der Statuswert ergibt sich aus der Summe der Bruttostromerzeugung aus Windenergie, "
                "Solarenergie, Wasserkraft einschließlich Tiefengeothermie sowie den biogenen Brennstoffen."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus der Summe der im Szenario angesetzten Bruttostromerzeugung "
                "aus allen erneuerbaren Teilbereichen einschließlich der rechnerisch anfallenden "
                "Abregelung."
            ),
            "sources": [],
        },
        "9.2": {
            "status": (
                "Der Statuswert entspricht der gesamten Bruttostromerzeugung aus erneuerbaren Energien "
                "einschließlich möglicher Abregelung."
            ),
            "ziel": (
                "Der Zielwert beschreibt die gesamte im Szenario erzeugte erneuerbare Strommenge "
                "einschließlich der Anteile, die später in Umwandlung, Speicherung oder Abregelung gehen."
            ),
            "sources": [],
        },
        "9.2.1": {
            "status": (
                "Die elektrolytische Erzeugung von Wasserstoff aus Wind- und Solarstrom ist im Status "
                "noch keine relevante Größe."
            ),
            "ziel": (
                "Im Zielbild wird überschüssiger erneuerbarer Strom per Wasserelektrolyse in Wasserstoff "
                "umgewandelt, um daraus Brennstoffe, synthetische Kraftstoffe und Grundstoffe bereitzustellen."
            ),
            "sources": [],
        },
        "9.2.1.1": {
            "status": (
                "Die elektrolytische Erzeugung von Wasserstoff für Prozesswärme ist im Status noch "
                "keine relevante Größe."
            ),
            "ziel": (
                "Auf Wasserstoff für Prozesswärme wird im Zielbild verzichtet. Wo möglich, wird "
                "Prozesswärme direkt elektrifiziert; für verbleibende Brennstoffanwendungen sind "
                "vor allem feste biogene Brennstoffe vorgesehen."
            ),
            "sources": [],
        },
        "9.2.1.1.1": {
            "status": "Direkt nutzbarer komprimierter Wasserstoff für Brennstoffzellen-Fahrzeuge ist im Status nicht relevant.",
            "ziel": (
                "Im Zielbild wird auf diesen Pfad verzichtet. Für mobile Anwendungen werden hier "
                "andere Optionen, insbesondere synthetische Flüssigkraftstoffe, priorisiert."
            ),
            "sources": [],
        },
        "9.2.1.1.1.1": {
            "status": "Im Status nicht relevant, da dieser Pfad derzeit nicht genutzt wird.",
            "ziel": (
                "Für Speicherung, Verteilung und Betankung von komprimiertem Wasserstoff mit 700 bar "
                "wird ein Nutzungsgrad von rund 80 % angesetzt."
            ),
            "sources": [
                {
                    "section": "ziel",
                    "label": "IFEU Wasserstoff",
                    "description": (
                        "Scharpf, Thomas, Energiebetrachtung zu Brennstoffzellen und Wasserstoff. "
                        "IFEU Interessengemeinschaft zur Förderung der Elektromobilität im Unterallgäu. "
                        "1. November 2017. Jüngster Zugriff am 03.04.2025."
                    ),
                    "url": "http://www.i-feu.de/I-FEU/Podcast/5B301566-15A0-460E-9BF0-71A5C655BBB4.html",
                },
            ],
        },
        "9.2.1.1.2": {
            "status": "Im Status nicht relevant, da direkt genutzter Wasserstoff für FC-Traktion derzeit nicht eingesetzt wird.",
            "ziel": (
                "Der Zielwert ergibt sich aus dem für Brennstoffzellen-Fahrzeuge vorgesehenen "
                "Wasserstoffpfad. Da dieser Pfad hier nicht genutzt wird, bleibt der Wert null."
            ),
            "sources": [],
        },
        "9.2.1.2": {
            "status": "Synthetisches Methan aus Wasserstoff für mobile Anwendungen ist im Status nicht relevant.",
            "ziel": (
                "Im Zielbild wird auf gasförmigen Kraftstoff aus Wasserstoff für mobile Anwendungen "
                "verzichtet. Stattdessen werden hier synthetische Flüssigkraftstoffe für die nicht "
                "elektrifizierbaren Restanwendungen priorisiert."
            ),
            "sources": [],
        },
        "9.2.1.2.1": {
            "status": "Im Status nicht relevant, da dieser Umwandlungspfad derzeit nicht genutzt wird.",
            "ziel": (
                "Für die Methanisierung von Wasserstoff wird ein optimistischer Nutzungsgrad von 80 % "
                "angesetzt."
            ),
            "sources": [
                {
                    "section": "ziel",
                    "label": "Leitstudie 2011",
                    "description": (
                        "BUNDESMINISTERIUM FÜR UMWELT, NATURSHUTZ UND REAKTORSICHERHEIT BMU (Hrsg.), "
                        "DLR, FRAUNHOFER IWES, IFNE (2012) \"Langfristszenarien und Strategien für den "
                        "Ausbau der erneuerbaren Energien in Deutschland bei Berücksichtigung der "
                        "Entwicklung in Europa und global\" (Leitstudie 2011 - Schlussbericht an das BMU). "
                        "Zugriff am 29.03.2015."
                    ),
                    "url": "https://elib.dlr.de/76043/",
                },
            ],
        },
        "9.2.1.2.2": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert ergibt sich aus dem Bedarf an synthetischem Methan für mobile Anwendungen "
                "und dem angesetzten Nutzungsgrad der Methansynthese."
            ),
            "sources": [],
        },
        "9.2.1.3": {
            "status": (
                "Synthetische flüssige Kraftstoffe aus erneuerbarem Wasserstoff sind im Status noch "
                "keine relevante Größe."
            ),
            "ziel": (
                "Für den nicht durch Elektrifizierung oder Biokraftstoffe abgedeckten Restbedarf der "
                "mobilen Anwendungen werden synthetische Flüssigkraftstoffe auf Basis von Wind- und "
                "Solarwasserstoff vorgesehen."
            ),
            "sources": [],
        },
        "9.2.1.3.1": {
            "status": "Im Status nicht relevant, da dieser Pfad derzeit nicht genutzt wird.",
            "ziel": (
                "Für die Erzeugung flüssiger Kraftstoffe aus Wasserstoff wird ein Nutzungsgrad von 63 % "
                "angesetzt. Gemeint sind vor allem synthetische Kraftstoffe wie Kerosin, Benzin und Diesel."
            ),
            "sources": [
                {
                    "section": "ziel",
                    "label": "FVV/LBST Kraftstoffstudie",
                    "description": (
                        "FORSCHUNGSVEREINIGUNG VERBRENNUNGSKRAFTMASCHINEN e. V. (2013): "
                        "\"Zukünftige Kraftstoffe für Verbrennungsmotoren und Gasturbinen\". Online am "
                        "02.04.2025 nicht mehr verfügbar."
                    ),
                    "url": "http://www.fvv-net.de/cms/upload/Download/FVV-Kraftstoffstudie_LBST_2013-10-30.pdf",
                },
            ],
        },
        "9.2.1.3.2": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert ergibt sich aus dem Bedarf an synthetischen Flüssigkraftstoffen und dem "
                "angenommenen Nutzungsgrad ihrer Herstellung aus Wasserstoff."
            ),
            "sources": [],
        },
        "9.2.1.4": {
            "status": (
                "Der heutige Bedarf an Kohlenwasserstoffen als Grundstoff der Chemieindustrie wird "
                "ausschließlich aus fossilen Quellen gedeckt."
            ),
            "ziel": (
                "Synthetisches Methan aus erneuerbarem Wasserstoff wird im Zielbild als Option für "
                "Grundstoffe vorgesehen, um fossile Kohlenwasserstoffe zu ersetzen, ohne die begrenzten "
                "stofflich nutzbaren Biomassepotenziale weiter zu belasten."
            ),
            "sources": [],
        },
        "9.2.1.4.1": {
            "status": "Im Status nicht relevant, da dieser Pfad derzeit nicht genutzt wird.",
            "ziel": "Für die Methanisierung von Wasserstoff zu Grundstoffzwecken wird ein Nutzungsgrad von 80 % angesetzt.",
            "sources": [
                {
                    "section": "ziel",
                    "label": "Leitstudie 2011",
                    "description": (
                        "BUNDESMINISTERIUM FÜR UMWELT, NATURSHUTZ UND REAKTORSICHERHEIT BMU (Hrsg.), "
                        "DLR, FRAUNHOFER IWES, IFNE (2012) \"Langfristszenarien und Strategien für den "
                        "Ausbau der erneuerbaren Energien in Deutschland bei Berücksichtigung der "
                        "Entwicklung in Europa und global\" (Leitstudie 2011 - Schlussbericht an das BMU). "
                        "Zugriff am 29.03.2015."
                    ),
                    "url": "https://elib.dlr.de/76043/",
                },
            ],
        },
        "9.2.1.4.2": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert ergibt sich aus dem vorgesehenen Methanbedarf für Grundstoffe und dem "
                "angesetzten Nutzungsgrad der Methansynthese."
            ),
            "sources": [],
        },
        "9.2.1.5": {
            "status": (
                "Die elektrolytische Wasserstofferzeugung aus erneuerbarem Strom ist im Status noch "
                "keine relevante Größe."
            ),
            "ziel": (
                "Der Zielwert ergibt sich aus dem gesamten Wasserstoffbedarf für synthetische "
                "Kraftstoffe, Grundstoffe und weitere vorgesehene Anwendungen im Szenario."
            ),
            "sources": [],
        },
        "9.2.1.5.1": {
            "status": (
                "Im Status wird ein Heizwert-bezogener Wirkungsgrad von 54,9 % angesetzt. Er resultiert "
                "aus einem brennwertbezogenen Elektrolyse-Wirkungsgrad von 64,9 % inklusive Einspeisung "
                "bei 80 bar."
            ),
            "ziel": (
                "Für das Zielbild wird ein Heizwert-bezogener Wirkungsgrad von 64 % angesetzt."
            ),
            "sources": [
                {
                    "section": "status",
                    "label": "DVGW Metastudie Wasserstoff",
                    "description": (
                        "Müller-Syring Gert et al.; Metastudie zur Untersuchung der Potenziale von "
                        "Wasserstoff für die Integration von Verkehrs- und Energiewirtschaft. DVGW "
                        "Deutscher Verein des Gas- und Wasserfaches e. V. Bonn, Oktober 2015. "
                        "Jüngster Zugriff am 03.04.2025."
                    ),
                    "url": "https://www.now-gmbh.de/wp-content/uploads/2020/09/dvgw-abschlussbericht-metastudie-2016-2.pdf",
                },
            ],
        },
        "9.2.1.5.2": {
            "status": "Im Status nicht relevant, da derzeit kein Elektrolysestrom für diesen Pfad eingesetzt wird.",
            "ziel": (
                "Der Zielwert ergibt sich aus der benötigten Wasserstoffmenge und dem angesetzten "
                "Wirkungsgrad der Wasserelektrolyse."
            ),
            "sources": [],
        },
        "9.2.1.5.2.1": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert beschreibt den Anteil des Elektrolysestroms, der im Zielbild direkt "
                "in der Zielregion bereitgestellt werden muss."
            ),
            "sources": [],
        },
        "9.2.1.5.2.2": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert beschreibt den Anteil des Elektrolysestroms, der gegebenenfalls außerhalb "
                "der Zielregion für Importwasserstoff bereitgestellt würde. In diesem Szenario bleibt er null."
            ),
            "sources": [],
        },
        "9.3": {
            "general": (
                "Mit steigenden Anteilen von Wind- und Solarstrom werden neben Kurzzeitspeichern auch "
                "Langzeitspeicher für Tage, Wochen und Monate notwendig. Im Szenario wird dazu "
                "überschüssiger Strom per Elektrolyse in Wasserstoff umgewandelt, unterirdisch "
                "gespeichert und in Mangelphasen wieder rückverstromt."
            ),
            "status": (
                "Eine Langzeitspeicherung von Strom über Wasserstoff ist im Status noch nicht erforderlich."
            ),
            "ziel": (
                "Im Zielbild übernimmt die stoffliche Langzeitspeicherung den saisonalen Ausgleich "
                "zwischen Überschuss- und Mangelphasen erneuerbarer Stromerzeugung."
            ),
            "sources": [],
        },
        "9.3.1": {
            "status": (
                "Eine Aufnahme von Stromüberschüssen für saisonale Langzeitspeicherung ist im Status "
                "noch nicht erforderlich."
            ),
            "ziel": (
                "Im Zielbild müssen große Überschussmengen an Strom in die Wasser-Elektrolyse geleitet "
                "werden, um genügend Wasserstoff für die Rückverstromung in Mangelphasen bereitzustellen."
            ),
            "sources": [],
        },
        "9.3.2": {
            "status": (
                "Im Status nicht relevant, da Langzeitstromspeicherung über Wasserstoff derzeit keine "
                "Rolle spielt."
            ),
            "ziel": (
                "Der Zielwert beschreibt den tatsächlich nutzbaren Anteil der KWK-Abwärme aus der "
                "Rückverstromung von Wasserstoff."
            ),
            "sources": [],
        },
        "9.3.2.1": {
            "status": "Im Status nicht relevant.",
            "ziel": (
                "Der Zielwert ergibt sich aus der im Szenario angenommenen nutzbaren KWK-Abwärme aus der "
                "Rückverstromung des gespeicherten Wasserstoffs."
            ),
            "sources": [],
        },
        "9.3.3": {
            "status": (
                "Eine saisonale Wasserstoff-Speicherkapazität für Langzeitstromspeicherung ist im Status "
                "noch nicht erforderlich."
            ),
            "ziel": (
                "Der Zielwert beschreibt die im Szenario mindestens erforderliche Wasserstoffspeicherkapazität "
                "für den saisonalen Ausgleich."
            ),
            "sources": [],
        },
        "9.3.4": {
            "status": (
                "Abregelung von Wind- und Solarstrom für die hier betrachtete Langzeitspeicherung ist im "
                "Status noch nicht relevant."
            ),
            "ziel": (
                "Trotz Elektrolysekapazität muss im Zielbild an Tagen mit besonders hohem Wind- oder "
                "Solarstromangebot ein Teil der Erzeugung abgeregelt werden."
            ),
            "sources": [],
        },
        "9.4": {
            "status": (
                "Der Statuswert beschreibt das verfügbare Stromangebot aus erneuerbaren Energien im "
                "Szenario nach den bilanzierten Umwandlungs- und Netzschritten."
            ),
            "ziel": (
                "Der Zielwert beschreibt das im Szenario verfügbare Stromangebot aus erneuerbaren "
                "Energien nach Berücksichtigung von Speicherung, Netzverlusten und sonstigen "
                "bilanzrelevanten Stromflüssen."
            ),
            "sources": [],
        },
        "9.4.1": {
            "status": "Der Statuswert beschreibt das Stromangebot aus eigenen erneuerbaren Energien.",
            "ziel": "Der Zielwert beschreibt das im Szenario verfügbare Stromangebot aus eigenen erneuerbaren Energien.",
            "sources": [],
        },
        "9.4.2": {
            "status": (
                "Die Einfuhr von Strom aus erneuerbaren Quellen von außerhalb Deutschlands ist im "
                "Status nicht relevant."
            ),
            "ziel": (
                "Im Zielbild wird keine Einfuhr von erneuerbarem Strom aus dem Ausland vorgesehen. "
                "Vorrang hat die eigene Versorgung auf Basis der inländischen Potenziale."
            ),
            "sources": [],
        },
        "9.4.3": {
            "status": (
                "Der Statuswert beschreibt das gesamte erneuerbare Stromangebot nach Berücksichtigung "
                "eigener Erzeugung und möglicher Einfuhr."
            ),
            "ziel": (
                "Der Zielwert beschreibt das gesamte erneuerbare Stromangebot des Szenarios vor Abzug "
                "der Netzverluste zur Endenergieseite."
            ),
            "sources": [],
        },
        "9.4.3.1": {
            "status": (
                "Die Netzverluste in Deutschland lagen im Status bei 5,5 %."
            ),
            "ziel": (
                "Für das Zielbild wird ein Netzverlustanteil von 9,2 % angesetzt. Ursache ist die "
                "stärkere Beanspruchung und Ausdehnung der künftigen Stromnetze."
            ),
            "sources": [],
        },
        "9.4.3.2": {
            "status": (
                "Der Statuswert beschreibt das erneuerbare Stromangebot einschließlich der Wirkung der "
                "Kurzzeitspeicher."
            ),
            "ziel": (
                "Der Zielwert beschreibt das erneuerbare Stromangebot einschließlich der im Szenario "
                "berücksichtigten Kurzzeitspeicher."
            ),
            "sources": [],
        },
        "9.4.3.3": {
            "status": (
                "Der Statuswert beschreibt das nach Netzverlusten verbleibende erneuerbare Stromangebot "
                "auf Endenergieebene."
            ),
            "ziel": (
                "Der Zielwert beschreibt das nach Berücksichtigung der Netzverluste verbleibende "
                "erneuerbare Stromangebot auf Endenergieebene."
            ),
            "sources": [],
        },
    }

    replacement = replacements.get(row_code)
    if replacement:
        note_parts["general_information"] = replacement.get("general", "")
        note_parts["status_information"] = replacement.get("status", "")
        note_parts["ziel_information"] = replacement.get("ziel", "")
        source_refs = replacement.get("sources", source_refs)

    note_parts["status_information"] = note_parts["status_information"].replace(
        "Gemäß einer Studie des Von Thünen-Instituts",
        "Gemäß einer Studie des Von-Thünen-Instituts",
    )
    note_parts["status_information"] = note_parts["status_information"].replace(
        "naturschtzorientierten",
        "naturschutzorientierten",
    )
    note_parts["ziel_information"] = note_parts["ziel_information"].replace(
        "naturschtzorientierten",
        "naturschutzorientierten",
    )
    note_parts["status_information"] = note_parts["status_information"].replace(
        "Verusacher- bzw. Solidarprinzip",
        "Verursacher- bzw. Solidarprinzip",
    )
    note_parts["ziel_information"] = note_parts["ziel_information"].replace(
        "Bioiesel",
        "Biodiesel",
    )
    note_parts["ziel_information"] = note_parts["ziel_information"].replace(
        "Biodethanol",
        "Bioethanol",
    )

    return note_parts, source_refs


def _immediate_hierarchical_children(model, row):
    explicit = list(
        model.all_objects.filter(owner__isnull=True, region=row.region, parent_code=row.code).order_by("code")
    )
    if explicit:
        return explicit

    code = (row.code or "").strip()
    if not code:
        return []

    base = code.rstrip(".")
    if not base:
        return []
    base_depth = base.count(".")
    prefix = f"{base}."

    children = []
    for candidate in model.all_objects.filter(owner__isnull=True, region=row.region, code__startswith=prefix).order_by("code"):
        candidate_code = (candidate.code or "").rstrip(".")
        if not candidate_code or candidate_code == base:
            continue
        if candidate_code.count(".") == base_depth + 1:
            children.append(candidate)
    return children


def _summarize_child_labels(children) -> str:
    labels = []
    for child in children[:4]:
        if child.code and child.name:
            labels.append(f"{child.code} {child.name}")
        elif child.name:
            labels.append(child.name)
        elif child.code:
            labels.append(child.code)
    return ", ".join(labels)


def _generic_renewable_note_parts(model, row) -> tuple[dict[str, str], list[dict]]:
    children = _immediate_hierarchical_children(model, row)
    child_summary = _summarize_child_labels(children)

    general = ""
    status = ""
    ziel = ""

    if children:
        general = "Diese Position bündelt die zugehörigen Unterpositionen."
        if child_summary:
            general += f" Relevante Unterpositionen sind: {child_summary}."

    if row.formula:
        if child_summary:
            status = (
                "Der Statuswert dieser Position wird rechnerisch aus den zugehörigen Unterpositionen "
                f"abgeleitet ({child_summary})."
            )
            ziel = (
                "Der Zielwert dieser Position wird rechnerisch aus den zugehörigen Unterpositionen "
                f"abgeleitet ({child_summary})."
            )
        else:
            status = "Der Statuswert dieser Position wird rechnerisch aus den im Modell hinterlegten Beziehungen abgeleitet."
            ziel = "Der Zielwert dieser Position wird rechnerisch aus den im Modell hinterlegten Beziehungen abgeleitet."
    elif children:
        status = (
            "Für diese Sammelposition ist kein eigener separater Status-Ansatz im D-Blatt hinterlegt. "
            "Sie dient vor allem der Gliederung und Zusammenfassung der Unterpositionen."
        )
        ziel = (
            "Für diese Sammelposition ist kein eigener separater Ziel-Ansatz im D-Blatt hinterlegt. "
            "Sie dient vor allem der Gliederung und Zusammenfassung der Unterpositionen."
        )
    else:
        status = (
            "Für diese Position liegt kein eigener separater Status-Ansatz im D-Blatt vor. "
            "Der Wert wird hier als technische bzw. abgeleitete Modellposition geführt."
        )
        ziel = (
            "Für diese Position liegt kein eigener separater Ziel-Ansatz im D-Blatt vor. "
            "Der Wert wird hier als technische bzw. abgeleitete Modellposition geführt."
        )

    return (
        {
            "general_information": general,
            "status_information": status,
            "ziel_information": ziel,
        },
        [],
    )


class Command(BaseCommand):
    help = (
        "Create admin-editable UI provenance override rows from the current "
        "shared row provenance already shown in the UI."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            choices=sorted(DOMAIN_MODEL_MAP.keys()),
            default="landuse",
            help="Which domain to backfill into UI provenance overrides.",
        )
        parser.add_argument(
            "--region",
            default="DE",
            help="Region code to backfill from (default: DE).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing override texts/source rows instead of only filling empty overrides.",
        )
        parser.add_argument(
            "--codes",
            default="",
            help="Optional comma-separated list of row codes to backfill.",
        )

    def handle(self, *args, **options):
        domain = options["domain"]
        region_code = options["region"]
        overwrite = options["overwrite"]
        selected_codes = [code.strip() for code in options.get("codes", "").split(",") if code.strip()]

        model = DOMAIN_MODEL_MAP[domain]
        try:
            region = Region.objects.get(code=region_code)
        except Region.DoesNotExist as exc:
            raise CommandError(f"Region '{region_code}' not found.") from exc

        if hasattr(model, "all_objects"):
            rows = model.all_objects.filter(owner__isnull=True, region=region).order_by("code")
        else:
            rows = model.objects.filter(region=region).order_by("code")
        if selected_codes:
            rows = rows.filter(code__in=selected_codes)

        created = 0
        updated = 0
        skipped = 0

        for row in rows:
            has_any_provenance = bool(
                getattr(row, "notes_assumption", None)
                or getattr(row, "source_url", None)
                or getattr(row, "source_refs", None)
            )
            has_manual_renewable_override = domain == "renewable" and row.code in RENEWABLE_MANUAL_OVERRIDE_CODES
            has_generic_renewable_override = domain == "renewable"
            if not has_any_provenance and not has_manual_renewable_override and not has_generic_renewable_override:
                skipped += 1
                continue

            override, was_created = UIProvenanceOverride.objects.get_or_create(
                region=region,
                domain=domain,
                row_code=row.code,
                defaults={
                    "row_label": getattr(row, "name", None) or getattr(row, "category", None) or "",
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

            has_existing_content = bool(
                override.general_information
                or override.status_information
                or override.ziel_information
                or override.sources.exists()
            )
            if has_existing_content and not overwrite:
                skipped += 1
                continue

            note_parts = split_notes_assumption_sections(_current_ui_note_text(row))
            if domain == "landuse":
                note_parts = _clean_landuse_note_parts(row.code, note_parts)
            source_refs = list(getattr(row, "source_refs", None) or [])
            if domain == "landuse":
                source_refs = [_clean_landuse_source(ref) for ref in source_refs]
            elif domain == "renewable":
                note_parts, source_refs = _clean_renewable_note_parts(row.code, note_parts, source_refs)
                source_refs = [_clean_renewable_source(ref) for ref in source_refs]
                if not any(note_parts.values()) and not source_refs:
                    note_parts, source_refs = _generic_renewable_note_parts(model, row)

            final_has_content = bool(
                note_parts["general_information"]
                or note_parts["status_information"]
                or note_parts["ziel_information"]
                or source_refs
                or getattr(row, "source_url", None)
            )
            if not final_has_content:
                skipped += 1
                continue

            override.row_label = getattr(row, "name", None) or getattr(row, "category", None) or override.row_label
            override.general_information = note_parts["general_information"]
            override.status_information = note_parts["status_information"]
            override.ziel_information = note_parts["ziel_information"]
            override.is_active = True
            override.save()

            override.sources.all().delete()
            for idx, ref in enumerate(source_refs):
                UIProvenanceSource.objects.create(
                    override=override,
                    section=ref.get("section") or "general",
                    label=ref.get("label") or "",
                    description=ref.get("description") or "",
                    url=ref.get("url") or "",
                    sort_order=idx,
                )

            if not was_created:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfilled UI provenance overrides for domain={domain}, region={region_code}: "
                f"created={created}, updated={updated}, skipped={skipped}"
            )
        )
