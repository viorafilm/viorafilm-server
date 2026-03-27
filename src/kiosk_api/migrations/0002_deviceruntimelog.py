from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("kiosk_api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceRuntimeLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("log_filename", models.CharField(max_length=255)),
                ("chunk_start", models.BigIntegerField(default=0)),
                ("chunk_end", models.BigIntegerField(default=0)),
                ("is_reset", models.BooleanField(default=False)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runtime_logs", to="core.device")),
            ],
            options={
                "indexes": [models.Index(fields=["device", "created_at"], name="kiosk_api_de_device__150020_idx")],
                "constraints": [
                    models.UniqueConstraint(fields=("device", "log_filename", "chunk_start", "chunk_end"), name="uniq_device_runtime_log_chunk"),
                ],
            },
        ),
    ]
