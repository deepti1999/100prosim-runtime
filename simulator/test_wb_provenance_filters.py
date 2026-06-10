from django.test import SimpleTestCase

from simulator.templatetags.provenance_filters import (
    clean_provenance_note,
    render_provenance_note,
)


class TestCleanProvenanceNote(SimpleTestCase):
    def test_removes_simple_and_extended_numeric_citations(self):
        raw = (
            "Gemäß GENESIS [9.224], Tabelle 33111-01-02-4. "
            "Siehe Windstudie [9.85, S. 21] und Leitfaden [9.182 Seite 9]. "
            "Interner Verweis [122] entfällt ebenfalls."
        )

        cleaned = clean_provenance_note(raw)

        self.assertNotIn("[9.224]", cleaned)
        self.assertNotIn("[9.85, S. 21]", cleaned)
        self.assertNotIn("[9.182 Seite 9]", cleaned)
        self.assertNotIn("[122]", cleaned)
        self.assertIn("Gemäß GENESIS, Tabelle 33111-01-02-4.", cleaned)


class TestRenderProvenanceNote(SimpleTestCase):
    def test_renders_solar_roof_note_with_meaningful_source_names(self):
        raw = (
            "- STATUS-Ansatz: Die solare Absorberfläche auf Dächern von 34.243 ha "
            "resultiert aus der Summe von solarthermischen Flach- und "
            "Röhrenkollektoren zur Wärmegewinnung gemäß [122] und "
            "Photovoltaikmodulen zur Stromgewinnung gemäß [123].\n\n"
            "Die solarthermischen Flach- und Röhrenkollektoren zur Wärmegewinnung "
            "belegten eine Fläche von 2178,5 ha gemäß [139].\n\n"
            "Insgesamt waren 2022 gemäß [9.4], PV-Leistung bauliche Anl., in "
            "Deutschland 47.857 MWp PV baulich installiert.\n\n"
            "- ZIEL-Ansatz: 199.398 ha solare Absorberfläche auf Dächern. Der Wert "
            "resultiert aus einer Studie von Agora Energiewende [9.17] nach "
            "Summierung der im Datenteil als Photovoltaikpotenzial auf Dachflächen "
            "in Deutschland gelisteten Modulflächen [127]."
        )
        source_refs = [
            {
                "section": "status",
                "label": "Solarthermie Kollektorfläche",
                "description": 'AGENTUR ERNEUERBARE ENERGIEN: "Wo stehen die Bundesländer beim Ausbau der Erneuerbaren Energien?"; Zugriff 23.01.2025',
            },
            {
                "section": "status",
                "label": "PV-Leistung bauliche Anl.",
                "description": 'AGENTUR ERNEUERBARE ENERGIEN: "Wo stehen die Bundesländer beim Ausbau der Erneuerbaren Energien?"; Zugriff 23.01.2025',
            },
            {
                "section": "ziel",
                "description": 'AGORA ENERGIEWENDE, Katarina Hartz (2023): "Solarstrom vom Dach: Das Energiewendepotenzial auf Deutschlands Gebäuden".',
            },
            {
                "section": "ziel",
                "url": "https://www.agora-energiewende.de/fileadmin/Projekte/2023/2023-16_DE_Dach-PV-Potenzial/PV_Potenziale_Datenanhang.xlsx",
            },
        ]

        rendered = render_provenance_note(raw, source_refs)

        self.assertIn("gemäß Solarthermie Kollektorfläche", rendered)
        self.assertIn("gemäß PV-Leistung bauliche Anl.", rendered)
        self.assertIn("gemäß PV-Leistung bauliche Anl., in Deutschland", rendered)
        self.assertIn("Studie von Agora Energiewende Solarstrom vom Dach", rendered)
        self.assertIn("PV_Potenziale_Datenanhang.xlsx", rendered)
        self.assertNotIn("[122]", rendered)
        self.assertNotIn("[123]", rendered)
        self.assertNotIn("[9.17]", rendered)
