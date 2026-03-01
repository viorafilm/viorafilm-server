import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from audit.service import log_event

from .models import Coupon, CouponBatch

MAX_COUPON_BATCH_COUNT = 1000
MAX_TOTAL_COUPONS = 3000

COUPON_EXPIRE_PRESETS_HOURS = {
    "1d": 24,
    "1w": 24 * 7,
    "1m": 24 * 30,
    "1y": 24 * 365,
}


def normalize_coupon_code(text) -> str:
    digits = "".join(ch for ch in str(text or "") if ch.isdigit())
    if len(digits) != 6:
        raise ValueError("Coupon code must be 6 digits")
    return digits


def _generate_unique_code(max_retries: int = 100) -> str:
    for _ in range(max_retries):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if not Coupon.objects.filter(code=code).exists():
            return code
    raise RuntimeError("Failed to generate unique coupon code")


def resolve_expires_hours(expires_period=None, expires_hours=24) -> int:
    key = str(expires_period or "").strip().lower()
    if key in COUPON_EXPIRE_PRESETS_HOURS:
        return int(COUPON_EXPIRE_PRESETS_HOURS[key])
    try:
        parsed = int(expires_hours or 24)
    except Exception:
        parsed = 24
    return 24 if parsed <= 0 else parsed


def _validate_issue_limits(requested_count: int) -> None:
    try:
        count = int(requested_count)
    except Exception:
        count = 0
    if count <= 0:
        raise ValueError("발행 수량은 1장 이상이어야 합니다.")
    if count > MAX_COUPON_BATCH_COUNT:
        raise ValueError(f"1회 발행 최대 수량은 {MAX_COUPON_BATCH_COUNT}장입니다.")

    current_total = int(Coupon.objects.count())
    remaining = int(MAX_TOTAL_COUPONS - current_total)
    if count > remaining:
        raise ValueError(
            f"전체 쿠폰 한도({MAX_TOTAL_COUPONS}장) 초과입니다. 현재 {current_total}장, 남은 {max(0, remaining)}장"
        )


def issue_coupons_for_batch(batch: CouponBatch, created_by=None):
    if batch.coupons.exists():
        return
    _validate_issue_limits(int(getattr(batch, "count", 0) or 0))
    now = timezone.now()
    expires_hours = resolve_expires_hours(expires_hours=getattr(batch, "expires_hours", 24))
    expires_at = now + timedelta(hours=expires_hours)
    created = 0
    with transaction.atomic():
        while created < int(batch.count):
            code = _generate_unique_code()
            try:
                Coupon.objects.create(
                    batch=batch,
                    code=code,
                    amount=batch.amount,
                    currency="KRW",
                    created_at=now,
                    expires_at=expires_at,
                )
                created += 1
            except IntegrityError:
                continue

    log_event(
        actor_user=created_by,
        actor_device=None,
        action="coupon.batch.issue",
        target_type="CouponBatch",
        target_id=str(batch.pk),
        before=None,
        after={
            "batch_id": batch.pk,
            "count": batch.count,
            "amount": batch.amount,
            "expires_hours": expires_hours,
            "org_id": batch.org_id,
            "branch_id": batch.branch_id,
        },
        meta={},
        ip=None,
    )


def create_batch_and_coupons(org, branch, amount, count, created_by, title="", expires_hours=24) -> CouponBatch:
    safe_count = int(count or 0)
    _validate_issue_limits(safe_count)
    safe_expires_hours = resolve_expires_hours(expires_hours=expires_hours)
    with transaction.atomic():
        batch = CouponBatch.objects.create(
            org=org,
            branch=branch,
            amount=int(amount),
            count=safe_count,
            expires_hours=safe_expires_hours,
            created_by=created_by,
            title=title or "",
        )
        issue_coupons_for_batch(batch=batch, created_by=created_by)
        return batch


def quote_coupon(code, amount_due):
    try:
        normalized = normalize_coupon_code(code)
    except ValueError:
        return False, 0, int(amount_due), "INVALID_FORMAT", None

    coupon = Coupon.objects.filter(code=normalized).select_related("batch").first()
    if not coupon:
        return False, 0, int(amount_due), "NOT_FOUND", None
    if coupon.is_used:
        return False, 0, int(amount_due), "USED", coupon
    if coupon.is_expired:
        return False, 0, int(amount_due), "EXPIRED", coupon

    amount_coupon = int(coupon.amount)
    remaining = max(0, int(amount_due) - amount_coupon)
    return True, amount_coupon, remaining, "OK", coupon


def redeem_coupon_atomic(device, code, session_id, amount_due, amount_coupon_expected=None):
    normalized = normalize_coupon_code(code)
    with transaction.atomic():
        coupon = Coupon.objects.select_for_update().filter(code=normalized).first()
        if not coupon:
            raise ValueError("COUPON_NOT_FOUND")
        if coupon.is_used:
            if coupon.used_by_device_id == device.id and coupon.used_session_id == session_id:
                return coupon
            raise ValueError("COUPON_ALREADY_USED")
        if coupon.is_expired:
            raise ValueError("COUPON_EXPIRED")
        if amount_coupon_expected is not None:
            try:
                expected_value = int(amount_coupon_expected)
            except Exception:
                expected_value = 0
            if expected_value > 0 and int(coupon.amount) != expected_value:
                raise ValueError("COUPON_AMOUNT_MISMATCH")
        if int(amount_due) <= 0:
            raise ValueError("INVALID_AMOUNT_DUE")

        coupon.used_at = timezone.now()
        coupon.used_by_device = device
        coupon.used_session_id = str(session_id)
        coupon.save(update_fields=["used_at", "used_by_device", "used_session_id"])

    log_event(
        actor_user=None,
        actor_device=device,
        action="coupon.redeem",
        target_type="Coupon",
        target_id=str(coupon.pk),
        before={"used_at": None, "used_by_device": None, "used_session_id": None},
        after={
            "used_at": coupon.used_at.isoformat() if coupon.used_at else None,
            "used_by_device": coupon.used_by_device_id,
            "used_session_id": coupon.used_session_id,
        },
        meta={"code": coupon.code},
        ip=None,
    )
    return coupon
