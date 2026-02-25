from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    actor_user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    actor_device = models.ForeignKey("core.Device", null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=128)
    target_type = models.CharField(max_length=128)
    target_id = models.CharField(max_length=128)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.created_at} {self.action} {self.target_type}:{self.target_id}"

