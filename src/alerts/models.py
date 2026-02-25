from django.db import models
from django.db.models import Q
from django.utils import timezone


class AlertType(models.TextChoices):
    OFFLINE = "OFFLINE", "OFFLINE"
    PRINTER_OFFLINE = "PRINTER_OFFLINE", "PRINTER_OFFLINE"
    CAMERA_OFFLINE = "CAMERA_OFFLINE", "CAMERA_OFFLINE"
    INTERNET_OFFLINE = "INTERNET_OFFLINE", "INTERNET_OFFLINE"


class Severity(models.TextChoices):
    INFO = "INFO", "INFO"
    WARN = "WARN", "WARN"
    CRITICAL = "CRITICAL", "CRITICAL"


class Alert(models.Model):
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=32, choices=AlertType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARN)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device", "alert_type"],
                condition=Q(resolved_at__isnull=True),
                name="alerts_one_open_alert_per_device_type",
            ),
        ]
        indexes = [
            models.Index(fields=["alert_type", "resolved_at"]),
        ]

    def is_open(self):
        return self.resolved_at is None


class ChannelType(models.TextChoices):
    SLACK = "SLACK", "SLACK"
    EMAIL = "EMAIL", "EMAIL"
    KAKAO = "KAKAO", "KAKAO"


class NotificationChannel(models.Model):
    org = models.ForeignKey("core.Organization", null=True, blank=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=16, choices=ChannelType.choices)
    enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
