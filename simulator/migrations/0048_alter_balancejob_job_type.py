from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0047_alter_balancejob_job_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="balancejob",
            name="job_type",
            field=models.CharField(
                choices=[
                    ("solar_sector_ws", "Sector + WS Solar Balance"),
                    ("wind_sector_ws", "Sector + WS Wind Balance"),
                    ("solar_ws_only", "WS Solar Balance"),
                    ("wind_ws_only", "WS Wind Balance"),
                    ("renewables_recalc", "Renewables Recalculation"),
                    ("verbrauch_recalc", "Verbrauch Recalculation"),
                    ("landuse_recalc", "LandUse Recalculation"),
                ],
                max_length=32,
            ),
        ),
    ]
