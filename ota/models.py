from django.conf import settings
from django.db import models
from django.db.models import Q


class AppRelease(models.Model):
    PLATFORM_WIN = "win"
    PLATFORM_CHOICES = (
        (PLATFORM_WIN, "Windows"),
    )

    platform = models.CharField(max_length=16, choices=PLATFORM_CHOICES, default=PLATFORM_WIN)
    version = models.CharField(max_length=64)  # e.g. 1.2.3
    is_active = models.BooleanField(default=False)
    min_supported_version = models.CharField(max_length=64, default="0.0.0")
    force_below_min = models.BooleanField(default=True)
    artifact = models.FileField(upload_to="releases/")
    sha256 = models.CharField(max_length=64)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_releases",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("platform", "-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("platform",),
                condition=Q(is_active=True),
                name="ota_one_active_release_per_platform",
            ),
            models.UniqueConstraint(
                fields=("platform", "version"),
                name="ota_unique_platform_version",
            ),
        ]

    def __str__(self) -> str:
        active_mark = " [ACTIVE]" if self.is_active else ""
        return f"{self.platform}:{self.version}{active_mark}"
