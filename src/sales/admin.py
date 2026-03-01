from datetime import datetime, timedelta

from django.contrib import admin
from django.utils import timezone

from .models import SaleTransaction

AI_EST_USD_PER_IMAGE = 0.039
AI_EST_KRW_PER_USD = 1400.0
AI_EST_DEFAULT_IMAGES_PER_SALE = 2
AI_EST_SERVER_COST_MULTIPLIER = 10.0
AI_EST_KRW_PER_IMAGE = int(round(AI_EST_USD_PER_IMAGE * AI_EST_KRW_PER_USD))


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    change_list_template = "admin/sales/saletransaction/change_list.html"
    list_display = (
        "created_at",
        "compose_mode",
        "ai_generated_count",
        "ai_billing_amount",
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

    @admin.display(description="ai_images")
    def ai_generated_count(self, obj):
        meta = obj.meta if isinstance(obj.meta, dict) else {}
        mode = str(meta.get("compose_mode", "normal")).strip().lower() or "normal"
        if mode != "ai":
            return 0
        try:
            count = int(meta.get("ai_generated_count", AI_EST_DEFAULT_IMAGES_PER_SALE) or 0)
        except Exception:
            count = AI_EST_DEFAULT_IMAGES_PER_SALE
        return max(0, count)

    @admin.display(description="ai_billing_est(KRW)")
    def ai_billing_amount(self, obj):
        images = int(self.ai_generated_count(obj) or 0)
        return int(round(images * AI_EST_KRW_PER_IMAGE * AI_EST_SERVER_COST_MULTIPLIER))

    def _resolve_billing_month(self, request):
        raw = str(request.GET.get("billing_month") or "").strip()
        today = timezone.localdate()
        default_month = today.replace(day=1)
        if not raw:
            return default_month
        try:
            parsed = datetime.strptime(raw, "%Y-%m").date()
            return parsed.replace(day=1)
        except Exception:
            return default_month

    def _billing_month_range(self, month_first):
        next_month = (month_first.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_last = next_month - timedelta(days=1)
        today = timezone.localdate()
        end_date = month_last
        if month_first.year == today.year and month_first.month == today.month:
            end_date = today
        return month_first, end_date, month_last

    def _build_monthly_ai_rows(self, qs, start_date, end_date):
        rows_by_branch = {}
        total_sales = 0
        total_images = 0
        for sale in qs.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).iterator():
            meta = sale.meta if isinstance(sale.meta, dict) else {}
            mode = str(meta.get("compose_mode", "normal")).strip().lower() or "normal"
            if mode != "ai":
                continue
            try:
                ai_images = int(meta.get("ai_generated_count", AI_EST_DEFAULT_IMAGES_PER_SALE) or 0)
            except Exception:
                ai_images = AI_EST_DEFAULT_IMAGES_PER_SALE
            if ai_images <= 0:
                ai_images = AI_EST_DEFAULT_IMAGES_PER_SALE
            total_sales += 1
            total_images += ai_images
            key = int(sale.branch_id or 0)
            row = rows_by_branch.get(key)
            if row is None:
                row = {
                    "org_code": getattr(sale.org, "code", "-"),
                    "branch_code": getattr(sale.branch, "code", "-"),
                    "branch_name": getattr(sale.branch, "name", "-"),
                    "ai_sales": 0,
                    "ai_images": 0,
                    "billing_amount": 0,
                }
                rows_by_branch[key] = row
            row["ai_sales"] += 1
            row["ai_images"] += ai_images

        rows = list(rows_by_branch.values())
        for row in rows:
            row["billing_amount"] = int(round(row["ai_images"] * AI_EST_KRW_PER_IMAGE * AI_EST_SERVER_COST_MULTIPLIER))
        rows.sort(key=lambda r: (str(r["org_code"]), str(r["branch_code"])))
        total_billing = int(round(total_images * AI_EST_KRW_PER_IMAGE * AI_EST_SERVER_COST_MULTIPLIER))
        return rows, total_sales, total_images, total_billing

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            cl = response.context_data["cl"]
            filtered_qs = cl.queryset
        except Exception:
            return response

        month = self._resolve_billing_month(request)
        start_date, end_date, month_last = self._billing_month_range(month)
        rows, total_sales, total_images, total_billing = self._build_monthly_ai_rows(
            filtered_qs,
            start_date,
            end_date,
        )
        response.context_data.update(
            {
                "ai_admin_billing_month_value": month.strftime("%Y-%m"),
                "ai_admin_billing_start_date": start_date.isoformat(),
                "ai_admin_billing_end_date": end_date.isoformat(),
                "ai_admin_billing_month_last": month_last.isoformat(),
                "ai_admin_rows": rows,
                "ai_admin_total_sales": total_sales,
                "ai_admin_total_images": total_images,
                "ai_admin_total_billing": total_billing,
            }
        )
        return response
