from django.db import models
from django.utils import timezone


class DeviceHeartbeat(models.Model):
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="heartbeats")
    created_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField(default=dict, blank=True)
    internet_ok = models.BooleanField(null=True, blank=True)
    camera_ok = models.BooleanField(null=True, blank=True)
    printer_ok = models.BooleanField(null=True, blank=True)

