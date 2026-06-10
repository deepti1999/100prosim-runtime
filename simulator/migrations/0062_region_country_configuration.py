# Additive country/region configuration.
#
# This does not move or recalculate existing Germany data. It only gives
# each Region the labels and planning years that templates/admin can read.
from django.db import migrations, models


def backfill_de_country_configuration(apps, schema_editor):
    Region = apps.get_model("simulator", "Region")
    Region.objects.filter(code="DE").update(
        locale_code="de-DE",
        status_year=2023,
        target_year=2045,
        goal_description="100 % Erneuerbare Energien",
        data_source_label="Anlagenpark Deutschland 2023 [SMARD]",
        total_area_ha=35759529.0,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0061_rename_admin_data_version_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="region",
            name="locale_code",
            field=models.CharField(blank=True, default="de-DE", max_length=16),
        ),
        migrations.AddField(
            model_name="region",
            name="status_year",
            field=models.PositiveIntegerField(default=2023),
        ),
        migrations.AddField(
            model_name="region",
            name="target_year",
            field=models.PositiveIntegerField(default=2045),
        ),
        migrations.AddField(
            model_name="region",
            name="goal_description",
            field=models.CharField(
                blank=True,
                default="100 % Erneuerbare Energien",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="region",
            name="data_source_label",
            field=models.CharField(
                blank=True,
                default="Anlagenpark Deutschland 2023 [SMARD]",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="region",
            name="total_area_ha",
            field=models.FloatField(default=35759529.0),
        ),
        migrations.RunPython(backfill_de_country_configuration, reverse_code=migrations.RunPython.noop),
    ]
