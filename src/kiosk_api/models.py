from django.db import models
from django.utils import timezone


class DeviceHeartbeat(models.Model):
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="heartbeats")
    created_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField(default=dict, blank=True)
    internet_ok = models.BooleanField(null=True, blank=True)
    camera_ok = models.BooleanField(null=True, blank=True)
    printer_ok = models.BooleanField(null=True, blank=True)


class DeviceRuntimeLog(models.Model):
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="runtime_logs")
    log_filename = models.CharField(max_length=255)
    chunk_start = models.BigIntegerField(default=0)
    chunk_end = models.BigIntegerField(default=0)
    is_reset = models.BooleanField(default=False)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["device", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "log_filename", "chunk_start", "chunk_end"],
                name="uniq_device_runtime_log_chunk",
            ),
        ]

