from django.db import models
from django.db.models import Q
from django.utils import timezone


class Platform(models.TextChoices):
    WIN = "win", "Windows"


class AppRelease(models.Model):
    platform = models.CharField(max_length=8, choices=Platform.choices, default=Platform.WIN)
    version = models.CharField(max_length=32)
    is_active = models.BooleanField(default=False)
    min_supported_version = models.CharField(max_length=32, default="0.0.0")
    force_below_min = models.BooleanField(default=True)

    artifact = models.FileField(upload_to="releases/")
    sha256 = models.CharField(max_length=64, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["platform", "is_active"])]
        constraints = [
            models.UniqueConstraint(
                fields=["platform"],
                condition=Q(is_active=True),
                name="ota_one_active_per_platform",
            ),
            models.UniqueConstraint(fields=["platform", "version"], name="ota_unique_platform_version"),
        ]

    def __str__(self):
        return f"{self.platform}:{self.version}{'*' if self.is_active else ''}"
