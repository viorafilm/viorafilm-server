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

