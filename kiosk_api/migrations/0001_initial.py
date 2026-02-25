# Generated manually for scaffold bootstrap.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceHeartbeat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("internet_ok", models.BooleanField(blank=True, null=True)),
                ("camera_ok", models.BooleanField(blank=True, null=True)),
                ("printer_ok", models.BooleanField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(on_delete=models.CASCADE, related_name="heartbeats", to="core.device"),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
