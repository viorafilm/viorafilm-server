from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_device_mode_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="install_bound_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="device",
            name="install_key_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="device",
            name="install_key_hint",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="device",
            name="last_install_seen_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
