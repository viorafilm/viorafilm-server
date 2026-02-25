from django.db import models
from django.db.models import Max
from django.utils import timezone


class ConfigScope(models.TextChoices):
    GLOBAL = "GLOBAL", "GLOBAL"
    ORG = "ORG", "ORG"
    BRANCH = "BRANCH", "BRANCH"
    DEVICE = "DEVICE", "DEVICE"


class ConfigProfile(models.Model):
    scope = models.CharField(max_length=16, choices=ConfigScope.choices)
    org = models.ForeignKey("core.Organization", null=True, blank=True, on_delete=models.CASCADE)
    branch = models.ForeignKey("core.Branch", null=True, blank=True, on_delete=models.CASCADE)
    device = models.ForeignKey("core.Device", null=True, blank=True, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=0)
    payload = models.JSONField(default=dict, blank=True)

    updated_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["scope", "version"]),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and (self.version is None or self.version == 0):
            qs = ConfigProfile.objects.filter(scope=self.scope, org=self.org, branch=self.branch, device=self.device)
            max_v = qs.aggregate(Max("version"))["version__max"] or 0
            self.version = max_v + 1
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

