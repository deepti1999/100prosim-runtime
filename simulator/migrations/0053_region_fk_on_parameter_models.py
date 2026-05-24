# Phase B (T65, SR-004) — region FK on the 4 parameter models +
# backfill all existing rows to DE + tighten the owner-scoped unique
# constraints to include region.
#
# Pattern: AddField nullable -> RunPython backfill -> AlterField
# non-null. Keeps the schema consistent at every step so PROTECT
# semantics are honoured and the live DB never has dangling FKs.
from django.db import migrations, models

import simulator.models


_MODELS_WITH_REGION_FK = [
    "landuse",
    "renewabledata",
    "verbrauchdata",
    "gebaeudewaermedata",
]


def backfill_region_to_DE(apps, schema_editor):
    """Set region_id = DE.pk on every parameter row that came in null.

    Covers both the 420 owner=NULL base rows and any per-user workspace
    rows that already exist (e.g. testsim from heroku_up.sh).
    """
    Region = apps.get_model("simulator", "Region")
    de = Region.objects.get(code="DE")
    for model_name in _MODELS_WITH_REGION_FK:
        Model = apps.get_model("simulator", model_name)
        Model.objects.filter(region__isnull=True).update(region=de)


def reverse_backfill(apps, schema_editor):
    # Reversal is a no-op: the AddField step would already be reverted
    # before this runs, dropping the column entirely.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0052_region_model_and_de_seed"),
    ]

    operations = [
        # 1) Add region FK as nullable so the table accepts the new
        #    column without violating PROTECT against existing rows.
        migrations.AddField(
            model_name="landuse",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AddField(
            model_name="renewabledata",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AddField(
            model_name="verbrauchdata",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AddField(
            model_name="gebaeudewaermedata",
            name="region",
            field=models.ForeignKey(
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        # 2) Backfill every row to DE.
        migrations.RunPython(backfill_region_to_DE, reverse_code=reverse_backfill),
        # 3) Tighten to non-null with the runtime default callable.
        migrations.AlterField(
            model_name="landuse",
            name="region",
            field=models.ForeignKey(
                default=simulator.models.get_default_region_pk,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AlterField(
            model_name="renewabledata",
            name="region",
            field=models.ForeignKey(
                default=simulator.models.get_default_region_pk,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AlterField(
            model_name="verbrauchdata",
            name="region",
            field=models.ForeignKey(
                default=simulator.models.get_default_region_pk,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        migrations.AlterField(
            model_name="gebaeudewaermedata",
            name="region",
            field=models.ForeignKey(
                default=simulator.models.get_default_region_pk,
                on_delete=models.PROTECT,
                related_name="+",
                to="simulator.region",
            ),
        ),
        # 4) Indexes.
        migrations.AddIndex(
            model_name="landuse",
            index=models.Index(fields=["region", "code"], name="simulator_l_region__f6399d_idx"),
        ),
        migrations.AddIndex(
            model_name="renewabledata",
            index=models.Index(fields=["region", "code"], name="simulator_r_region__1ce3ac_idx"),
        ),
        migrations.AddIndex(
            model_name="verbrauchdata",
            index=models.Index(fields=["region", "code"], name="simulator_v_region__24fc3c_idx"),
        ),
        migrations.AddIndex(
            model_name="gebaeudewaermedata",
            index=models.Index(fields=["region", "code"], name="simulator_g_region__59cb80_idx"),
        ),
        # 5) Tighten owner-scoped unique constraints to include region
        #    so the same code (e.g. LU_2.1) can coexist across regions.
        migrations.RemoveConstraint(
            model_name="landuse",
            name="landuse_owner_code_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="landuse",
            name="landuse_global_code_uniq",
        ),
        migrations.AddConstraint(
            model_name="landuse",
            constraint=models.UniqueConstraint(
                fields=("owner", "region", "code"),
                name="landuse_owner_region_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="landuse",
            constraint=models.UniqueConstraint(
                fields=("region", "code"),
                condition=models.Q(owner__isnull=True),
                name="landuse_global_region_code_uniq",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="renewabledata",
            name="renewable_owner_code_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="renewabledata",
            name="renewable_global_code_uniq",
        ),
        migrations.AddConstraint(
            model_name="renewabledata",
            constraint=models.UniqueConstraint(
                fields=("owner", "region", "code"),
                condition=models.Q(code__isnull=False) & ~models.Q(code=""),
                name="renewable_owner_region_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="renewabledata",
            constraint=models.UniqueConstraint(
                fields=("region", "code"),
                condition=models.Q(owner__isnull=True, code__isnull=False) & ~models.Q(code=""),
                name="renewable_global_region_code_uniq",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="verbrauchdata",
            name="verbrauch_owner_code_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="verbrauchdata",
            name="verbrauch_global_code_uniq",
        ),
        migrations.AddConstraint(
            model_name="verbrauchdata",
            constraint=models.UniqueConstraint(
                fields=("owner", "region", "code"),
                name="verbrauch_owner_region_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="verbrauchdata",
            constraint=models.UniqueConstraint(
                fields=("region", "code"),
                condition=models.Q(owner__isnull=True),
                name="verbrauch_global_region_code_uniq",
            ),
        ),
    ]
