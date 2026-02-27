from rest_framework import serializers

from storagehub.models import UploadKind
from storagehub.service import normalize_kind


class HeartbeatSerializer(serializers.Serializer):
    app_version = serializers.CharField(required=False, allow_blank=True)
    internet_ok = serializers.BooleanField(required=False)
    camera_ok = serializers.BooleanField(required=False)
    printer_ok = serializers.BooleanField(required=False)
    film_remaining = serializers.IntegerField(required=False, min_value=0)
    printer_film_remaining = serializers.IntegerField(required=False, min_value=0)
    media_remaining = serializers.IntegerField(required=False, min_value=0)
    remaining_media = serializers.IntegerField(required=False, min_value=0)
    printer_ds620 = serializers.DictField(required=False)
    printer_rx1hs = serializers.DictField(required=False)
    last_error = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    offline_guard_enabled = serializers.BooleanField(required=False)
    offline_lock_active = serializers.BooleanField(required=False)
    offline_grace_seconds = serializers.IntegerField(required=False)
    offline_grace_remaining_seconds = serializers.IntegerField(required=False, allow_null=True)
    offline_reference_source = serializers.CharField(required=False, allow_blank=True)
    offline_last_online_at = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    offline_first_seen_at = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ConfigAppliedSerializer(serializers.Serializer):
    config_version = serializers.CharField()
    applied_at = serializers.DateTimeField(required=False)


class ShareCreateSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False, allow_blank=True)


class ShareCompleteSerializer(serializers.Serializer):
    token = serializers.CharField()
    assets = serializers.DictField()


class ShareUploadInitSerializer(serializers.Serializer):
    token = serializers.CharField(required=False, allow_blank=True)
    session_id = serializers.CharField(required=False, allow_blank=True)


class ShareUploadFileSerializer(serializers.Serializer):
    token = serializers.CharField()
    kind = serializers.CharField()
    file = serializers.FileField()

    def validate_kind(self, value):
        kind = normalize_kind(value)
        allowed = {k for k, _ in UploadKind.choices}
        if kind not in allowed:
            raise serializers.ValidationError(f"Unsupported kind: {value}")
        return kind


class ShareFinalizeSerializer(serializers.Serializer):
    token = serializers.CharField()
    meta = serializers.DictField(required=False, default=dict)


class CouponCheckSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()
    amount_due = serializers.IntegerField(min_value=0)


class SaleCompleteSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    layout_id = serializers.CharField()
    prints = serializers.IntegerField(required=False, default=2, min_value=1)
    currency = serializers.CharField(required=False, default="KRW")
    price_total = serializers.IntegerField(min_value=0)
    payment_method = serializers.CharField()
    amount_cash = serializers.IntegerField(required=False, default=0, min_value=0)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    amount_coupon = serializers.IntegerField(required=False, default=0, min_value=0)
    meta = serializers.DictField(required=False, default=dict)
