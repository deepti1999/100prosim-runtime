# Phase B (T65, SR-004) — Region first-class model + DE seed.
# Additive: no existing column touched. Default DE row carries the
# installed-power constants that close T54 D4a / D4b (194 / 261 GW).
from django.db import migrations, models


def seed_DE_region(apps, schema_editor):
    """Insert the DE row so existing single-region behaviour is preserved."""
    Region = apps.get_model("simulator", "Region")
    Region.objects.update_or_create(
        code="DE",
        defaults={
            "display_name": "Deutschland",
            "active": True,
            "datenmodell_excel_hash": "",
            "installed_pmax_ely_gw": 194.0,
            "installed_pmax_rv_gw": 261.0,
        },
    )


def unseed_DE_region(apps, schema_editor):
    Region = apps.get_model("simulator", "Region")
    Region.objects.filter(code="DE").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0051_phase_a_provenance_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Region",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=16, unique=True)),
                ("display_name", models.CharField(max_length=100)),
                ("active", models.BooleanField(default=True)),
                (
                    "datenmodell_excel_hash",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                ("installed_pmax_ely_gw", models.FloatField(default=0.0)),
                ("installed_pmax_rv_gw", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.RunPython(seed_DE_region, reverse_code=unseed_DE_region),
    ]
