# Phase C (T66) — drop GebaeudewaermeData.code's global unique=True
# in favour of UniqueConstraint(['region','code']) so per-Bundesland
# building data with the same code can coexist.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0053_region_fk_on_parameter_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gebaeudewaermedata",
            name="code",
            field=models.CharField(max_length=20),
        ),
        migrations.AddConstraint(
            model_name="gebaeudewaermedata",
            constraint=models.UniqueConstraint(
                fields=("region", "code"),
                name="gebaeudewaerme_region_code_uniq",
            ),
        ),
    ]
