import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from audit.service import log_event

from .models import Coupon, CouponBatch


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


def issue_coupons_for_batch(batch: CouponBatch, created_by=None):
    if batch.coupons.exists():
        return
    now = timezone.now()
    expires_at = now + timedelta(hours=24)
    created = 0
    while created < batch.count:
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
            "org_id": batch.org_id,
            "branch_id": batch.branch_id,
        },
        meta={},
        ip=None,
    )


def create_batch_and_coupons(org, branch, amount, count, created_by, title="") -> CouponBatch:
    with transaction.atomic():
        batch = CouponBatch.objects.create(
            org=org,
            branch=branch,
            amount=int(amount),
            count=int(count),
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


def redeem_coupon_atomic(device, code, session_id, amount_due, amount_coupon_expected):
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
        if int(coupon.amount) != int(amount_coupon_expected):
            raise ValueError("COUPON_AMOUNT_MISMATCH")
        if int(amount_due) < int(coupon.amount):
            raise ValueError("COUPON_EXCEEDS_DUE")

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

