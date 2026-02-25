from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from core.models import Branch, Device, Organization


class ConfigProfile(models.Model):
    SCOPE_GLOBAL = "GLOBAL"
    SCOPE_ORG = "ORG"
    SCOPE_BRANCH = "BRANCH"
    SCOPE_DEVICE = "DEVICE"

    SCOPE_CHOICES = (
        (SCOPE_GLOBAL, "Global"),
        (SCOPE_ORG, "Organization"),
        (SCOPE_BRANCH, "Branch"),
        (SCOPE_DEVICE, "Device"),
    )

    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES)
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="config_profiles",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="config_profiles",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="config_profiles",
    )
    version = models.PositiveIntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_config_profiles",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scope", "-version", "-updated_at")
        constraints = [
            models.UniqueConstraint(
                fields=("scope", "version"),
                condition=Q(scope=SCOPE_GLOBAL),
                name="configs_profile_global_unique_version",
            ),
            models.UniqueConstraint(
                fields=("scope", "org", "version"),
                condition=Q(scope=SCOPE_ORG),
                name="configs_profile_org_unique_version",
            ),
            models.UniqueConstraint(
                fields=("scope", "branch", "version"),
                condition=Q(scope=SCOPE_BRANCH),
                name="configs_profile_branch_unique_version",
            ),
            models.UniqueConstraint(
                fields=("scope", "device", "version"),
                condition=Q(scope=SCOPE_DEVICE),
                name="configs_profile_device_unique_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.scope} v{self.version or 0}"

    def clean(self):
        super().clean()
        if self.scope == self.SCOPE_GLOBAL:
            if self.org_id or self.branch_id or self.device_id:
                raise ValidationError("GLOBAL scope must not set org/branch/device.")
        elif self.scope == self.SCOPE_ORG:
            if not self.org_id or self.branch_id or self.device_id:
                raise ValidationError("ORG scope requires org only.")
        elif self.scope == self.SCOPE_BRANCH:
            if not self.branch_id or self.device_id:
                raise ValidationError("BRANCH scope requires branch only.")
        elif self.scope == self.SCOPE_DEVICE:
            if not self.device_id:
                raise ValidationError("DEVICE scope requires device.")
        else:
            raise ValidationError("Invalid scope.")

    def _version_base_queryset(self):
        qs = ConfigProfile.objects.filter(scope=self.scope)
        if self.scope == self.SCOPE_GLOBAL:
            return qs.filter(org__isnull=True, branch__isnull=True, device__isnull=True)
        if self.scope == self.SCOPE_ORG:
            return qs.filter(org_id=self.org_id, branch__isnull=True, device__isnull=True)
        if self.scope == self.SCOPE_BRANCH:
            return qs.filter(branch_id=self.branch_id, device__isnull=True)
        if self.scope == self.SCOPE_DEVICE:
            return qs.filter(device_id=self.device_id)
        return qs.none()

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.version:
            with transaction.atomic():
                latest = (
                    self._version_base_queryset()
                    .exclude(pk=self.pk)
                    .select_for_update()
                    .order_by("-version")
                    .first()
                )
                self.version = int(getattr(latest, "version", 0) or 0) + 1
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)
