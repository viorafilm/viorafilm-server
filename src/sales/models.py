from django.conf import settings
from django.db import models
from django.utils import timezone


class SaleTransaction(models.Model):
    METHOD_CASH = "CASH"
    METHOD_CARD = "CARD"
    METHOD_COUPON = "COUPON"
    METHOD_COUPON_CASH = "COUPON_CASH"
    METHOD_TEST = "TEST"
    PAYMENT_CHOICES = (
        (METHOD_CASH, "CASH"),
        (METHOD_CARD, "CARD"),
        (METHOD_COUPON, "COUPON"),
        (METHOD_COUPON_CASH, "COUPON_CASH"),
        (METHOD_TEST, "TEST"),
    )

    org = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="sales")
    branch = models.ForeignKey("core.Branch", on_delete=models.CASCADE, related_name="sales")
    device = models.ForeignKey("core.Device", on_delete=models.CASCADE, related_name="sales")

    session_id = models.CharField(max_length=128)
    layout_id = models.CharField(max_length=32)
    prints = models.IntegerField(default=2)
    currency = models.CharField(max_length=8, default="KRW")
    price_total = models.IntegerField()

    payment_method = models.CharField(max_length=16, choices=PAYMENT_CHOICES)
    amount_cash = models.IntegerField(default=0)
    amount_coupon = models.IntegerField(default=0)
    coupon = models.ForeignKey("coupons.Coupon", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales")
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["device", "session_id"], name="uniq_sale_device_session"),
        ]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["org", "branch", "device"]),
        ]

    def __str__(self):
        return f"{self.device.device_code}:{self.session_id} {self.price_total}"


class BranchMonthlyBilling(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
    )

    org = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="monthly_billings")
    branch = models.ForeignKey("core.Branch", on_delete=models.CASCADE, related_name="monthly_billings")
    billing_month = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=255, blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_monthly_billings",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "billing_month"],
                name="uniq_branch_monthly_billing",
            ),
        ]
        indexes = [
            models.Index(fields=["billing_month", "status"]),
            models.Index(fields=["org", "branch"]),
        ]

    def __str__(self):
        return f"{self.branch.code}:{self.billing_month.isoformat()}:{self.status}"
