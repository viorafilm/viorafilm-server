from django.contrib import admin

from .models import SaleTransaction


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "compose_mode",
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

    @admin.display(description="compose_mode")
    def compose_mode(self, obj):
        meta = obj.meta if isinstance(obj.meta, dict) else {}
        mode = str(meta.get("compose_mode", "normal")).strip().lower() or "normal"
        if mode not in {"normal", "ai", "celebrity"}:
            mode = "normal"
        return mode
