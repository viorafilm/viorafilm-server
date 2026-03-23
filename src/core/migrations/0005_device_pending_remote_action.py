from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_device_install_binding"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="pending_remote_action",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="device",
            name="pending_remote_action_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
