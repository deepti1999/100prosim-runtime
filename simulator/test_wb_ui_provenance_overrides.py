from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from simulator.models import LandUse, Region, RenewableData, UIProvenanceOverride, UIProvenanceSource
from simulator.ui_provenance_service import split_notes_assumption_sections


class UIProvenanceOverrideTests(TestCase):
    def setUp(self):
        self.region = Region.objects.get(code="DE")

    def test_build_notes_assumption_combines_general_status_and_ziel_sections(self):
        override = UIProvenanceOverride.objects.create(
            region=self.region,
            domain="landuse",
            row_code="LU_1.1",
            row_label="Solare Dachflächen",
            general_information="Allgemeine Erklärung.",
            status_information="Status-Text.",
            ziel_information="- ZIEL-Ansatz: Bereits fertig formuliert.",
        )

        built = override.build_notes_assumption()

        self.assertIn("Allgemeine Erklärung.", built)
        self.assertIn("- STATUS-Ansatz: Status-Text.", built)
        self.assertIn("- ZIEL-Ansatz: Bereits fertig formuliert.", built)

    def test_build_source_refs_returns_ordered_ui_payload(self):
        override = UIProvenanceOverride.objects.create(
            region=self.region,
            domain="landuse",
            row_code="LU_1.1",
            row_label="Solare Dachflächen",
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="ziel",
            label="Zielquelle",
            description="Quelle fuer Ziel.",
            url="https://example.com/ziel",
            sort_order=2,
        )
        UIProvenanceSource.objects.create(
            override=override,
            section="status",
            label="Statusquelle",
            description="Quelle fuer Status.",
            url="https://example.com/status",
            sort_order=1,
        )

        refs = override.build_source_refs()

        self.assertEqual(refs[0]["section"], "status")
        self.assertEqual(refs[0]["label"], "Statusquelle")
        self.assertEqual(refs[1]["section"], "ziel")
        self.assertEqual(override.primary_source_url(), "https://example.com/status")

    def test_split_notes_assumption_sections_extracts_status_and_ziel(self):
        parts = split_notes_assumption_sections(
            "Einleitung.\n\n- STATUS-Ansatz: Status text.\n\n- ZIEL-Ansatz: Ziel text."
        )

        self.assertEqual(parts["general_information"], "Einleitung.")
        self.assertEqual(parts["status_information"], "Status text.")
        self.assertEqual(parts["ziel_information"], "Ziel text.")

    def test_backfill_command_copies_current_landuse_ui_provenance_into_override(self):
        row = LandUse.objects.create(
            code="LU_0",
            name="Bodenfläche gesamt",
            status_ha=35759529.0,
            target_ha=35759529.0,
            notes_assumption=(
                "- STATUS-Ansatz: Gemäß GENESIS [9.224], Tabelle 33111-01-02-4.\n\n"
                "- ZIEL-Ansatz: Ziel bleibt identisch."
            ),
            source_refs=[
                {
                    "section": "status",
                    "label": "33111-01-02-4",
                    "description": "Regionaldatenbank Deutschland",
                    "url": "https://example.com/genesis",
                }
            ],
        )

        out = StringIO()
        call_command(
            "backfill_ui_provenance_overrides",
            "--domain",
            "landuse",
            "--region",
            "DE",
            stdout=out,
        )

        override = UIProvenanceOverride.objects.get(domain="landuse", row_code=row.code, region=self.region)
        self.assertEqual(override.row_label, "Bodenfläche gesamt")
        self.assertEqual(override.status_information, "Gemäß GENESIS, Tabelle 33111-01-02-4.")
        self.assertEqual(override.ziel_information, "Ziel bleibt identisch.")
        self.assertNotIn("[9.224]", override.status_information)
        self.assertEqual(override.sources.count(), 1)
        self.assertIn("created=1", out.getvalue())

    def test_backfill_command_rewrites_derived_renewable_rows_into_clear_formula_text(self):
        row = RenewableData.objects.create(
            code="4.1.3",
            name="Energieholzaufkommen gesamt",
            region=self.region,
            notes_assumption="#REF!\n\n#REF!",
            source_refs=[
                {
                    "section": "status",
                    "label": "Falsche Quelle",
                    "description": "Should be removed for derived admin text.",
                    "url": "https://example.com/wrong",
                }
            ],
        )

        out = StringIO()
        call_command(
            "backfill_ui_provenance_overrides",
            "--domain",
            "renewable",
            "--region",
            "DE",
            "--codes",
            row.code,
            stdout=out,
        )

        override = UIProvenanceOverride.objects.get(domain="renewable", row_code=row.code, region=self.region)
        self.assertEqual(
            override.status_information,
            "Der Statuswert ergibt sich aus der Summe des Energieholzaufkommens aus Forstwirtschaft und aus Ackerbau.",
        )
        self.assertEqual(
            override.ziel_information,
            "Der Zielwert ergibt sich aus der Summe des Ziel-Aufkommens aus Forstwirtschaft und aus Ackerbau.",
        )
        self.assertEqual(override.sources.count(), 0)
        self.assertIn("created=1", out.getvalue())

    def test_backfill_command_creates_manual_renewable_heatpump_override_even_without_imported_provenance(self):
        row = RenewableData.objects.create(
            category="Geothermie",
            code="8.2",
            name="Gebäudewärmebereitstellung (Endenergie)",
            unit="GWh/a",
            region=self.region,
            notes_assumption=None,
            source_refs=[],
            source_url="",
        )

        out = StringIO()
        call_command(
            "backfill_ui_provenance_overrides",
            "--domain",
            "renewable",
            "--region",
            "DE",
            "--codes",
            row.code,
            stdout=out,
        )

        override = UIProvenanceOverride.objects.get(domain="renewable", row_code=row.code, region=self.region)
        self.assertEqual(
            override.status_information,
            "Die Bereitstellung von Gebäudewärme aus Tiefengeothermie lag 2023 in Deutschland bei 1.797 GWh.",
        )
        self.assertIn("Für das Zieljahr werden 12.000 GWh angenommen.", override.ziel_information)
        self.assertEqual(override.sources.count(), 3)
        self.assertIn("created=1", out.getvalue())

    def test_backfill_command_creates_manual_renewable_storage_override(self):
        row = RenewableData.objects.create(
            category="Speicherung",
            code="9.3.1",
            name="Stromaufnahme (Überschussphasen)",
            unit="GWh/a",
            region=self.region,
            notes_assumption=None,
            source_refs=[],
            source_url="",
        )

        out = StringIO()
        call_command(
            "backfill_ui_provenance_overrides",
            "--domain",
            "renewable",
            "--region",
            "DE",
            "--codes",
            row.code,
            stdout=out,
        )

        override = UIProvenanceOverride.objects.get(domain="renewable", row_code=row.code, region=self.region)
        self.assertEqual(
            override.status_information,
            "Eine Aufnahme von Stromüberschüssen für saisonale Langzeitspeicherung ist im Status noch nicht erforderlich.",
        )
        self.assertIn("Im Zielbild müssen große Überschussmengen an Strom", override.ziel_information)
        self.assertEqual(override.sources.count(), 0)
        self.assertIn("created=1", out.getvalue())

    def test_backfill_command_creates_generic_renewable_formula_override_when_no_d_note_exists(self):
        row = RenewableData.objects.create(
            category="Test",
            code="99.1",
            name="Abgeleitete Testposition",
            unit="GWh/a",
            formula="A+B",
            region=self.region,
            notes_assumption=None,
            source_refs=[],
            source_url="",
        )

        out = StringIO()
        call_command(
            "backfill_ui_provenance_overrides",
            "--domain",
            "renewable",
            "--region",
            "DE",
            "--codes",
            row.code,
            stdout=out,
        )

        override = UIProvenanceOverride.objects.get(domain="renewable", row_code=row.code, region=self.region)
        self.assertIn("rechnerisch", override.status_information)
        self.assertIn("rechnerisch", override.ziel_information)
        self.assertEqual(override.sources.count(), 0)
        self.assertIn("created=1", out.getvalue())
