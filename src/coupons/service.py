import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from audit.service import log_event
from sales.models import SaleTransaction

from .legacy_old import get_legacy_old_coupon_record
from .models import Coupon, CouponBatch

MAX_COUPON_BATCH_COUNT = 1000
MAX_TOTAL_COUPONS = 3000

COUPON_EXPIRE_PRESETS_HOURS = {
    "1d": 24,
    "1w": 24 * 7,
    "1m": 24 * 30,
    "1y": 24 * 365,
}


def normalize_coupon_code(text, *, allowed_lengths=(6, 8)) -> str:
    digits = "".join(ch for ch in str(text or "") if ch.isdigit())
    normalized_lengths: list[int] = []
    for value in allowed_lengths:
        try:
            parsed = int(value)
        except Exception:
            continue
        if parsed > 0 and parsed not in normalized_lengths:
            normalized_lengths.append(parsed)
    if not normalized_lengths:
        normalized_lengths = [6]
    if len(digits) not in normalized_lengths:
        label = " or ".join(str(length) for length in normalized_lengths)
        raise ValueError(f"Coupon code must be {label} digits")
    return digits


def _coupon_queryset(*, lock: bool = False):
    queryset = Coupon.objects.select_related("batch")
    if lock:
        queryset = queryset.select_for_update()
    return queryset


def _build_legacy_coupon_meta(record) -> dict:
    return {
        "legacy_old_coupon": True,
        "legacy_source_file": record.source_file,
        "legacy_row_number": record.row_number,
        "legacy_group_name": record.group_name,
        "legacy_branch_name": record.branch_name,
        "legacy_raw_code": record.raw_code,
        "legacy_used_flag": "Y" if record.used else "N",
        "legacy_imported_at": timezone.now().isoformat(),
    }


def _ensure_legacy_coupon_imported(code: str, *, lock: bool = False):
    normalized = normalize_coupon_code(code, allowed_lengths=(8,))
    queryset = _coupon_queryset(lock=lock)
    coupon = queryset.filter(code=normalized).first()
    if coupon:
        return coupon

    record = get_legacy_old_coupon_record(normalized)
    if record is None:
        return None

    create_kwargs = {
        "batch": None,
        "code": normalized,
        "amount": int(record.amount),
        "currency": "KRW",
        "created_at": record.issued_at or timezone.now(),
        "expires_at": record.expires_at,
        "used_at": timezone.now() if record.used else None,
        "meta": _build_legacy_coupon_meta(record),
    }
    try:
        Coupon.objects.create(**create_kwargs)
    except IntegrityError:
        pass

    queryset = _coupon_queryset(lock=lock)
    coupon = queryset.filter(code=normalized).first()
    if coupon:
        fields_to_update: list[str] = []
        if int(coupon.amount or 0) <= 0 and int(record.amount or 0) > 0:
            coupon.amount = int(record.amount)
            fields_to_update.append("amount")
        if coupon.expires_at != record.expires_at:
            coupon.expires_at = record.expires_at
            fields_to_update.append("expires_at")
        merged_meta = {**dict(coupon.meta or {}), **_build_legacy_coupon_meta(record)}
        if merged_meta != dict(coupon.meta or {}):
            coupon.meta = merged_meta
            fields_to_update.append("meta")
        if record.used and coupon.used_at is None:
            coupon.used_at = timezone.now()
            fields_to_update.append("used_at")
        if fields_to_update:
            coupon.save(update_fields=fields_to_update)
    return coupon


def _resolve_coupon(code: str, *, lock: bool = False):
    normalized = normalize_coupon_code(code, allowed_lengths=(6, 8))
    queryset = _coupon_queryset(lock=lock)
    coupon = queryset.filter(code=normalized).first()
    if coupon:
        return normalized, coupon
    if len(normalized) == 8:
        coupon = _ensure_legacy_coupon_imported(normalized, lock=lock)
    return normalized, coupon


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
        raise ValueError("발행 수량은 1개 이상이어야 합니다.")
    if count > MAX_COUPON_BATCH_COUNT:
        raise ValueError(f"1회 발행 최대 수량은 {MAX_COUPON_BATCH_COUNT}개입니다.")

    current_total = int(Coupon.objects.count())
    remaining = int(MAX_TOTAL_COUPONS - current_total)
    if count > remaining:
        raise ValueError("전체 쿠폰 발행 한도를 초과했습니다. 시스템 관리 한도를 확인해 주세요.")


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
        normalized = normalize_coupon_code(code, allowed_lengths=(6, 8))
    except ValueError:
        return False, 0, int(amount_due), "INVALID_FORMAT", None

    _normalized, coupon = _resolve_coupon(normalized, lock=False)
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
    normalized = normalize_coupon_code(code, allowed_lengths=(6, 8))
    with transaction.atomic():
        _normalized, coupon = _resolve_coupon(normalized, lock=True)
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


def recover_coupon_usage_from_sales(*, actor_user=None, org_id=None, branch_id=None, ip=None):
    """
    Best-effort recovery for legacy rows where sale was saved but coupon linkage/used flag was missing.
    Scope can be restricted by org/branch.
    """
    qs = SaleTransaction.objects.select_related("device", "coupon").filter(
        Q(payment_method__in=[SaleTransaction.METHOD_COUPON, SaleTransaction.METHOD_COUPON_CASH])
        | Q(amount_coupon__gt=0)
    )
    if org_id is not None:
        qs = qs.filter(org_id=org_id)
    if branch_id is not None:
        qs = qs.filter(branch_id=branch_id)

    stats = {
        "scanned": 0,
        "linked_sales": 0,
        "coupon_marked_used": 0,
        "skipped_no_code": 0,
        "skipped_invalid_code": 0,
        "skipped_not_found": 0,
        "skipped_conflict": 0,
    }

    for sale in qs.order_by("created_at").iterator():
        stats["scanned"] += 1
        if sale.coupon_id:
            coupon = sale.coupon
            if coupon and not coupon.used_at:
                coupon.used_at = sale.created_at or timezone.now()
                coupon.used_by_device = sale.device
                coupon.used_session_id = sale.session_id
                coupon.save(update_fields=["used_at", "used_by_device", "used_session_id"])
                stats["coupon_marked_used"] += 1
            continue

        meta = sale.meta if isinstance(sale.meta, dict) else {}
        raw_code = str(meta.get("kiosk_coupon_code") or meta.get("coupon_code") or "").strip()
        if not raw_code:
            stats["skipped_no_code"] += 1
            continue
        try:
            normalized = normalize_coupon_code(raw_code, allowed_lengths=(6, 8))
        except ValueError:
            stats["skipped_invalid_code"] += 1
            continue

        with transaction.atomic():
            _normalized, coupon = _resolve_coupon(normalized, lock=True)
            if not coupon:
                stats["skipped_not_found"] += 1
                continue
            if coupon.used_at and not (
                coupon.used_session_id == sale.session_id and coupon.used_by_device_id == sale.device_id
            ):
                stats["skipped_conflict"] += 1
                continue

            if not coupon.used_at:
                coupon.used_at = sale.created_at or timezone.now()
                coupon.used_by_device = sale.device
                coupon.used_session_id = sale.session_id
                coupon.save(update_fields=["used_at", "used_by_device", "used_session_id"])
                stats["coupon_marked_used"] += 1

            sale.coupon = coupon
            if int(sale.amount_coupon or 0) <= 0:
                sale.amount_coupon = min(int(sale.price_total or 0), int(coupon.amount or 0))
            if int(sale.amount_cash or 0) < 0:
                sale.amount_cash = 0
            if sale.payment_method not in (SaleTransaction.METHOD_COUPON, SaleTransaction.METHOD_COUPON_CASH):
                sale.payment_method = (
                    SaleTransaction.METHOD_COUPON
                    if int(sale.amount_cash or 0) <= 0
                    else SaleTransaction.METHOD_COUPON_CASH
                )
            sale.save(update_fields=["coupon", "amount_coupon", "amount_cash", "payment_method"])
            stats["linked_sales"] += 1

    log_event(
        actor_user=actor_user,
        actor_device=None,
        action="coupon.recover_usage",
        target_type="SaleTransaction",
        target_id="bulk",
        before=None,
        after=stats,
        meta={"org_id": org_id, "branch_id": branch_id},
        ip=ip,
    )
    return stats
