from django.contrib import admin

from .models import SaleTransaction


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "org",
        "branch",
        "device",
        "session_id",
        "layout_id",
        "price_total",
        "payment_method",
        "amount_cash",
        "amount_coupon",
        "coupon",
    )
    list_filter = ("org", "branch", "device", "payment_method", "created_at")
    search_fields = ("session_id", "device__device_code", "layout_id")

