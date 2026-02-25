from django.db import models
from django.db.models import Q

from core.models import Device, Organization


class Alert(models.Model):
    TYPE_OFFLINE = "OFFLINE"
    TYPE_PRINTER_OFFLINE = "PRINTER_OFFLINE"
    TYPE_CAMERA_OFFLINE = "CAMERA_OFFLINE"
    TYPE_INTERNET_OFFLINE = "INTERNET_OFFLINE"
    TYPE_CHOICES = (
        (TYPE_OFFLINE, "Device Offline"),
        (TYPE_PRINTER_OFFLINE, "Printer Offline"),
        (TYPE_CAMERA_OFFLINE, "Camera Offline"),
        (TYPE_INTERNET_OFFLINE, "Internet Offline"),
    )

    SEVERITY_INFO = "INFO"
    SEVERITY_WARN = "WARN"
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_CHOICES = (
        (SEVERITY_INFO, "Info"),
        (SEVERITY_WARN, "Warn"),
        (SEVERITY_CRITICAL, "Critical"),
    )

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default=SEVERITY_WARN)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("device", "alert_type"),
                condition=Q(resolved_at__isnull=True),
                name="alerts_one_open_alert_per_type",
            ),
        ]
        indexes = [
            models.Index(fields=["device", "alert_type", "resolved_at"]),
            models.Index(fields=["resolved_at"]),
        ]

    def __str__(self) -> str:
        state = "RESOLVED" if self.resolved_at else "OPEN"
        return f"{self.device.device_code} {self.alert_type} ({state})"


class NotificationChannel(models.Model):
    TYPE_SLACK = "SLACK"
    TYPE_EMAIL = "EMAIL"
    TYPE_KAKAO = "KAKAO"
    TYPE_CHOICES = (
        (TYPE_SLACK, "Slack"),
        (TYPE_EMAIL, "Email"),
        (TYPE_KAKAO, "Kakao"),
    )

    org = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notification_channels",
    )
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("type", "id")

    def __str__(self) -> str:
        scope = self.org.code if self.org_id else "GLOBAL"
        return f"{scope}:{self.type}:{'ON' if self.enabled else 'OFF'}"
