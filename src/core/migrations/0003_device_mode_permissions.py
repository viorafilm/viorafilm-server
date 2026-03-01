from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_device_lock_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="allow_ai_mode",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="device",
            name="allow_celebrity_mode",
            field=models.BooleanField(default=True),
        ),
    ]

