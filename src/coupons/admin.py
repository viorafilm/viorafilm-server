from django.contrib import admin
from django.utils import timezone

from audit.service import log_event

from .models import Coupon, CouponBatch
from .service import issue_coupons_for_batch


@admin.register(CouponBatch)
class CouponBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "org", "branch", "amount", "count", "created_by", "created_at")
    list_filter = ("org", "branch", "created_at")
    search_fields = ("title", "org__code", "branch__code")

    def save_model(self, request, obj, form, change):
        obj.created_by = obj.created_by or request.user
        super().save_model(request, obj, form, change)
        if not change:
            issue_coupons_for_batch(obj, created_by=request.user)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "formatted_code",
        "amount",
        "currency",
        "expires_at",
        "used_at",
        "used_by_device",
        "used_session_id",
    )
    list_filter = ("currency", "used_at", "expires_at", "batch__org", "batch__branch")
    search_fields = ("code", "used_session_id", "used_by_device__device_code")
    actions = ("delete_expired", "delete_used")

    def delete_queryset(self, request, queryset):
        ids = list(queryset.values_list("id", flat=True))
        count = len(ids)
        super().delete_queryset(request, queryset)
        if count:
            log_event(
                actor_user=request.user,
                actor_device=None,
                action="coupon.delete",
                target_type="Coupon",
                target_id="admin-delete-queryset",
                before={"coupon_ids": ids},
                after={"deleted": count},
                meta={},
                ip=request.META.get("REMOTE_ADDR"),
            )

    def delete_model(self, request, obj):
        cid = obj.id
        super().delete_model(request, obj)
        log_event(
            actor_user=request.user,
            actor_device=None,
            action="coupon.delete",
            target_type="Coupon",
            target_id=str(cid),
            before={"coupon_id": cid},
            after={"deleted": 1},
            meta={},
            ip=request.META.get("REMOTE_ADDR"),
        )

    @admin.action(description="Delete expired coupons")
    def delete_expired(self, request, queryset):
        targets = queryset.filter(expires_at__lte=timezone.now(), used_at__isnull=True)
        count = targets.count()
        ids = list(targets.values_list("id", flat=True))
        targets.delete()
        if count:
            log_event(
                actor_user=request.user,
                actor_device=None,
                action="coupon.delete",
                target_type="Coupon",
                target_id="bulk-expired",
                before={"coupon_ids": ids},
                after={"deleted": count},
                meta={"scope": "admin_action_expired"},
                ip=request.META.get("REMOTE_ADDR"),
            )

    @admin.action(description="Delete used coupons")
    def delete_used(self, request, queryset):
        targets = queryset.filter(used_at__isnull=False)
        count = targets.count()
        ids = list(targets.values_list("id", flat=True))
        targets.delete()
        if count:
            log_event(
                actor_user=request.user,
                actor_device=None,
                action="coupon.delete",
                target_type="Coupon",
                target_id="bulk-used",
                before={"coupon_ids": ids},
                after={"deleted": count},
                meta={"scope": "admin_action_used"},
                ip=request.META.get("REMOTE_ADDR"),
            )
