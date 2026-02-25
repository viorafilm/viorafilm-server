import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_type", models.CharField(choices=[("OFFLINE", "OFFLINE"), ("PRINTER_OFFLINE", "PRINTER_OFFLINE"), ("CAMERA_OFFLINE", "CAMERA_OFFLINE"), ("INTERNET_OFFLINE", "INTERNET_OFFLINE")], max_length=32)),
                ("severity", models.CharField(choices=[("INFO", "INFO"), ("WARN", "WARN"), ("CRITICAL", "CRITICAL")], default="WARN", max_length=16)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("last_notified_at", models.DateTimeField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="core.device"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NotificationChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("SLACK", "SLACK"), ("EMAIL", "EMAIL"), ("KAKAO", "KAKAO")], max_length=16)),
                ("enabled", models.BooleanField(default=True)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "org",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="core.organization"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["alert_type", "resolved_at"], name="alerts_aler_alert_t_e4180e_idx"),
        ),
        migrations.AddConstraint(
            model_name="alert",
            constraint=models.UniqueConstraint(
                fields=("device", "alert_type"),
                condition=Q(resolved_at__isnull=True),
                name="alerts_one_open_alert_per_device_type",
            ),
        ),
    ]
