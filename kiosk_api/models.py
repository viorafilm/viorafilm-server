from django.db import models

from core.models import Device


class DeviceHeartbeat(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="heartbeats")
    created_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)
    internet_ok = models.BooleanField(null=True, blank=True)
    camera_ok = models.BooleanField(null=True, blank=True)
    printer_ok = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.device.device_code} @ {self.created_at.isoformat()}"
