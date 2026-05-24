from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulator", "0040_baselinesnapshot"),
    ]

    operations = [
        migrations.AlterField(
            model_name="renewabledata",
            name="unit",
            field=models.CharField(max_length=50),
        ),
    ]
