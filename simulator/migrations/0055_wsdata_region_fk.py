# Phase C (T66) — WSData per-(owner, region). Same AddField nullable
# -> RunPython backfill -> AlterField non-null pattern as Phase B 0053.
from django.db import migrations, models

import simulator.ws_models


def backfill_wsdata_region_to_DE(apps, schema_editor):
    Region = apps.get_model("simulator", "Region")
    WSData = apps.get_model("simulator", "WSData")
    de = Region.objects.get(code="DE")
    WSData.objects.filter(region__isnull=True).update(region=de)


def reverse_backfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0054_gebaeudewaerme_region_code_uniq"),
    ]

    operations = [
        migrations.AddField(
            model_name="wsdata",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.RunPython(backfill_wsdata_region_to_DE, reverse_code=reverse_backfill),
        migrations.AlterField(
            model_name="wsdata",
            name="region",
            field=models.ForeignKey(
                default=simulator.ws_models._ws_default_region_pk,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AddIndex(
            model_name="wsdata",
            index=models.Index(fields=["region", "tag_im_jahr"], name="simulator_w_region__40c1aa_idx"),
        ),
        migrations.RemoveConstraint(
            model_name="wsdata",
            name="wsdata_owner_day_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="wsdata",
            name="wsdata_global_day_uniq",
        ),
        migrations.AddConstraint(
            model_name="wsdata",
            constraint=models.UniqueConstraint(
                fields=("owner", "region", "tag_im_jahr"),
                name="wsdata_owner_region_day_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="wsdata",
            constraint=models.UniqueConstraint(
                fields=("region", "tag_im_jahr"),
                condition=models.Q(owner__isnull=True),
                name="wsdata_global_region_day_uniq",
            ),
        ),
    ]
