import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone

from core.models import Device


def default_share_expiry():
    return timezone.now() + timedelta(hours=24)


def generate_share_token(length: int = 32) -> str:
    while True:
        token = secrets.token_urlsafe(length)
        if not ShareSession.objects.filter(token=token).exists():
            return token


class ShareSession(models.Model):
    token = models.CharField(max_length=128, unique=True, db_index=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="share_sessions")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_share_expiry)
    assets = models.JSONField(default=dict, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.device.device_code}:{self.token[:8]}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

