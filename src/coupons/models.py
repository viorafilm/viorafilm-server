from datetime import timedelta

from django.db import models
from django.utils import timezone


def _default_expires_at():
    return timezone.now() + timedelta(hours=24)


class CouponBatch(models.Model):
    org = models.ForeignKey("core.Organization", null=True, blank=True, on_delete=models.SET_NULL)
    branch = models.ForeignKey("core.Branch", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, blank=True, default="")
    amount = models.IntegerField(default=0)
    count = models.IntegerField(default=0)
    expires_hours = models.PositiveIntegerField(default=24)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        scope = self.branch.code if self.branch else (self.org.code if self.org else "GLOBAL")
        return f"{scope} {self.amount}x{self.count}"


class Coupon(models.Model):
    STATUS_UNUSED = "UNUSED"
    STATUS_USED = "USED"
    STATUS_EXPIRED = "EXPIRED"

    batch = models.ForeignKey(CouponBatch, on_delete=models.CASCADE, related_name="coupons")
    code = models.CharField(max_length=6, unique=True)
    amount = models.IntegerField(default=0)
    currency = models.CharField(max_length=8, default="KRW")
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=_default_expires_at)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by_device = models.ForeignKey("core.Device", null=True, blank=True, on_delete=models.SET_NULL)
    used_session_id = models.CharField(max_length=128, null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["expires_at"]),
            models.Index(fields=["used_at"]),
        ]

    @property
    def formatted_code(self) -> str:
        return f"{self.code[:3]}-{self.code[3:]}" if len(self.code) == 6 else self.code

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def status(self) -> str:
        if self.is_used:
            return self.STATUS_USED
        if self.is_expired:
            return self.STATUS_EXPIRED
        return self.STATUS_UNUSED

    def __str__(self):
        return f"{self.formatted_code} ({self.amount} {self.currency})"
