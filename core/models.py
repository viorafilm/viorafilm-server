import hashlib
import secrets

from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40)

    class Meta:
        ordering = ("org__name", "name")
        constraints = [
            models.UniqueConstraint(fields=("org", "code"), name="core_branch_code_per_org_unique"),
        ]

    def __str__(self) -> str:
        return f"{self.org.code}/{self.code}"


class Device(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="devices")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="devices")
    device_code = models.CharField(max_length=32, unique=True)  # ex: PFQ4V43Z
    display_name = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)

    token_hash = models.CharField(max_length=64, blank=True, default="")
    token_hint = models.CharField(max_length=32, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_app_version = models.CharField(max_length=64, null=True, blank=True)
    last_config_version_applied = models.CharField(max_length=64, null=True, blank=True)
    last_health_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("device_code",)

    def __str__(self) -> str:
        return self.device_code

    def rotate_token(self) -> str:
        if not self.pk:
            raise ValueError("Device must be saved before rotating token.")
        raw_token = secrets.token_urlsafe(32)
        self.token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        self.token_hint = raw_token[-6:]
        self.save(update_fields=["token_hash", "token_hint", "updated_at"])
        return raw_token
