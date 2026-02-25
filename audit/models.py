from django.conf import settings
from django.db import models

from core.models import Device


class AuditEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    actor_device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120)
    target_id = models.CharField(max_length=120)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"{self.action} {self.target_type}:{self.target_id}"
