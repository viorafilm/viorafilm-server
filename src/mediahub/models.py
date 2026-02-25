import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ShareSession(models.Model):
    STATUS_INIT = "init"
    STATUS_UPLOADING = "uploading"
    STATUS_FINALIZED = "finalized"
    STATUS_CHOICES = (
        (STATUS_INIT, "Init"),
        (STATUS_UPLOADING, "Uploading"),
        (STATUS_FINALIZED, "Finalized"),
    )

    token = models.CharField(max_length=64, unique=True, db_index=True)
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_INIT)
    files = models.JSONField(default=dict, blank=True)
    assets = models.JSONField(default=dict, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(24)

    @classmethod
    def create_24h(cls, device, assets=None):
        now = timezone.now()
        ttl_hours = int(getattr(settings, "SHARE_TOKEN_TTL_HOURS", 24))
        return cls.objects.create(
            token=cls.new_token(),
            device=device,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            status=cls.STATUS_INIT,
            files={},
            assets=assets or {},
        )

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
