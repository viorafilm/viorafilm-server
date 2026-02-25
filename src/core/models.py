import hashlib
import hmac
import secrets

from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.name}({self.code})"


class Branch(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "code"], name="uniq_branch_code_per_org"),
        ]

    def __str__(self):
        return f"{self.name}({self.code})"


class Device(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="devices")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="devices")
    device_code = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    token_hash = models.CharField(max_length=64, blank=True, default="")
    token_hint = models.CharField(max_length=16, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_app_version = models.CharField(max_length=32, null=True, blank=True)
    last_config_version_applied = models.CharField(max_length=64, null=True, blank=True)
    last_config_applied_at = models.DateTimeField(null=True, blank=True)
    last_health_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.device_code}"

    def rotate_token(self) -> str:
        raw = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.token_hash = hashed
        self.token_hint = raw[-6:]
        self.save(update_fields=["token_hash", "token_hint", "updated_at"])
        return raw

    def verify_token(self, raw: str) -> bool:
        if not self.token_hash:
            return False
        hashed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return hmac.compare_digest(hashed, self.token_hash)
