# Generated manually for scaffold bootstrap.
import django.db.models.deletion
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
                (
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("OFFLINE", "Device Offline"),
                            ("PRINTER_OFFLINE", "Printer Offline"),
                            ("CAMERA_OFFLINE", "Camera Offline"),
                            ("INTERNET_OFFLINE", "Internet Offline"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[("INFO", "Info"), ("WARN", "Warn"), ("CRITICAL", "Critical")],
                        default="WARN",
                        max_length=16,
                    ),
                ),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("last_notified_at", models.DateTimeField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="core.device",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="NotificationChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("SLACK", "Slack"), ("EMAIL", "Email"), ("KAKAO", "Kakao")], max_length=16)),
                ("enabled", models.BooleanField(default=True)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "org",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_channels",
                        to="core.organization",
                    ),
                ),
            ],
            options={
                "ordering": ("type", "id"),
            },
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["device", "alert_type", "resolved_at"], name="alerts_aler_device__7ebe6a_idx"),
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["resolved_at"], name="alerts_aler_resolve_8e960d_idx"),
        ),
        migrations.AddConstraint(
            model_name="alert",
            constraint=models.UniqueConstraint(
                fields=("device", "alert_type"),
                condition=Q(resolved_at__isnull=True),
                name="alerts_one_open_alert_per_type",
            ),
        ),
    ]
