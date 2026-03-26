from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_device_pending_remote_action"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="offline_unlock_grace_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
