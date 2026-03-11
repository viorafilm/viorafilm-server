import csv
from datetime import datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo, available_timezones

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import UserRole
from alerts.notifier import send_email_targets
from alerts.models import ChannelType, NotificationChannel
from audit.service import log_event
from configs.models import ConfigProfile, ConfigScope
from core.models import Branch, Device, Organization
from coupons.models import Coupon
from coupons.service import (
    MAX_COUPON_BATCH_COUNT,
    MAX_TOTAL_COUPONS,
    create_batch_and_coupons,
    recover_coupon_usage_from_sales,
    resolve_expires_hours,
)
from kiosk_api.models import DeviceHeartbeat
from mediahub.models import ShareSession
from sales.models import BranchMonthlyBilling, SaleTransaction
from storagehub.models import UploadAsset
from storagehub.service import generate_download_url_from_meta
from urllib.parse import urlencode
from dashboard.ui import (
    can_manage_billing,
    format_dashboard_amount,
    get_dashboard_text,
    resolve_dashboard_currency_unit,
    resolve_dashboard_lang,
)

AI_EST_USD_PER_IMAGE = 0.039
AI_EST_KRW_PER_USD = 1400.0
AI_EST_DEFAULT_IMAGES_PER_SALE = 2
AI_EST_SERVER_COST_MULTIPLIER = 10.0
AI_EST_KRW_PER_IMAGE = int(round(AI_EST_USD_PER_IMAGE * AI_EST_KRW_PER_USD))
MONTHLY_SERVER_FEE_PER_DEVICE = 60000
COUPON_PER_PAGE_OPTIONS = (10, 30, 50, 100)
DASHBOARD_TIMEZONE_KEY = "dashboard_timezone"
DEFAULT_DASHBOARD_TIMEZONE = "Asia/Seoul"
PREFERRED_DASHBOARD_TIMEZONES = (
    "Asia/Seoul",
    "Asia/Tokyo",
    "Asia/Kolkata",
    "Asia/Singapore",
    "Asia/Bangkok",
    "Asia/Dubai",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Pacific/Auckland",
    "UTC",
)


def _is_super(user):
    return bool(getattr(user, "is_superuser", False)) or getattr(user, "role", None) == UserRole.SUPERADMIN


def _is_org_admin(user):
    return getattr(user, "role", None) == UserRole.ORG_ADMIN


def _can_manage_billing(user):
    return can_manage_billing(user)


def _is_branch_admin(user):
    return getattr(user, "role", None) == UserRole.BRANCH_ADMIN


def _is_viewer(user):
    if getattr(user, "is_superuser", False):
        return False
    return getattr(user, "role", None) == UserRole.VIEWER


def _scoped_devices(user):
    qs = Device.objects.select_related("org", "branch").order_by("-last_seen_at")
    if _is_super(user):
        return qs
    if _is_org_admin(user):
        return qs.filter(org=user.organization) if user.organization_id else qs.none()
    if _is_branch_admin(user):
        return qs.filter(branch=user.branch) if user.branch_id else qs.none()
    if user.branch_id:
        return qs.filter(branch=user.branch)
    if user.organization_id:
        return qs.filter(org=user.organization)
    return qs.none()


def _scoped_sales(user):
    qs = SaleTransaction.objects.select_related("org", "branch", "device", "coupon").order_by("-created_at")
    if _is_super(user):
        return qs
    if _is_org_admin(user):
        return qs.filter(org=user.organization) if user.organization_id else qs.none()
    if _is_branch_admin(user):
        return qs.filter(branch=user.branch) if user.branch_id else qs.none()
    if user.branch_id:
        return qs.filter(branch=user.branch)
    if user.organization_id:
        return qs.filter(org=user.organization)
    return qs.none()


def _scoped_coupons(user):
    qs = Coupon.objects.select_related("batch", "batch__org", "batch__branch", "used_by_device").order_by("-created_at")
    if _is_super(user):
        return qs
    if _is_org_admin(user):
        return qs.filter(batch__org=user.organization) if user.organization_id else qs.none()
    if _is_branch_admin(user):
        return qs.filter(batch__branch=user.branch) if user.branch_id else qs.none()
    if user.branch_id:
        return qs.filter(batch__branch=user.branch)
    if user.organization_id:
        return qs.filter(batch__org=user.organization)
    return qs.none()


def _available_orgs(user):
    if _is_super(user):
        return Organization.objects.order_by("name")
    if user.organization_id:
        return Organization.objects.filter(id=user.organization_id)
    return Organization.objects.none()


def _available_branches(user):
    if _is_super(user):
        return Branch.objects.select_related("org").order_by("org__name", "name")
    if _is_org_admin(user) and user.organization_id:
        return Branch.objects.select_related("org").filter(org=user.organization).order_by("name")
    if user.branch_id:
        return Branch.objects.select_related("org").filter(id=user.branch_id)
    return Branch.objects.none()


def _derive_printer_ok(health):
    if not isinstance(health, dict):
        return None
    direct = health.get("printer_ok")
    if isinstance(direct, bool):
        return direct
    values = []
    for key in ("printer_ds620", "printer_rx1hs"):
        item = health.get(key)
        if isinstance(item, dict) and isinstance(item.get("ok"), bool):
            values.append(item.get("ok"))
    if not values:
        return None
    return any(values)


def _as_optional_int(value):
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _extract_film_remaining(health):
    if not isinstance(health, dict):
        return None

    direct_keys = (
        "film_remaining",
        "printer_film_remaining",
        "media_remaining",
        "remaining_media",
    )
    for key in direct_keys:
        val = _as_optional_int(health.get(key))
        if val is not None and val >= 0:
            return val

    for key in ("printer_ds620", "printer_rx1hs"):
        item = health.get(key)
        if not isinstance(item, dict):
            continue
        for sub_key in ("film_remaining", "media_remaining", "remaining", "remain"):
            val = _as_optional_int(item.get(sub_key))
            if val is not None and val >= 0:
                return val

    return None


def _format_duration_compact(total_seconds: int) -> str:
    seconds = max(0, int(total_seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def _parse_email_list(text: str):
    raw = str(text or "").replace(";", ",")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    cleaned = []
    seen = set()
    for item in parts:
        if "@" not in item:
            continue
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(item)
    return cleaned


def _notification_scope_org(user):
    if _is_super(user):
        return None
    if getattr(user, "organization_id", None):
        return user.organization
    if getattr(user, "branch_id", None) and getattr(user.branch, "org_id", None):
        return user.branch.org
    return None


def _get_scope_email_channels(user):
    org = _notification_scope_org(user)
    query = NotificationChannel.objects.filter(type=ChannelType.EMAIL)
    if org is None:
        query = query.filter(org__isnull=True)
    else:
        query = query.filter(org=org)
    return query.order_by("id")


def _get_scope_email_targets(user):
    targets = []
    for channel in _get_scope_email_channels(user):
        value = channel.config.get("to")
        if isinstance(value, str) and value.strip():
            targets.append(value.strip())
    seen = set()
    deduped = []
    for email in targets:
        low = email.lower()
        if low in seen:
            continue
        seen.add(low)
        deduped.append(email)
    return deduped


def _pick_valid_int(value):
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except Exception:
        return None


def _latest_config_profile(scope, org=None, branch=None, device=None):
    return ConfigProfile.objects.filter(scope=scope, org=org, branch=branch, device=device).order_by("-version").first()


def _normalize_dashboard_timezone_name(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        ZoneInfo(raw)
        return raw
    except Exception:
        return None


def _default_dashboard_timezone_name():
    return _normalize_dashboard_timezone_name(getattr(settings, "TIME_ZONE", "")) or DEFAULT_DASHBOARD_TIMEZONE


def _load_dashboard_tzinfo(value=None):
    resolved = _normalize_dashboard_timezone_name(value) or _default_dashboard_timezone_name()
    try:
        return resolved, ZoneInfo(resolved)
    except Exception:
        fallback = DEFAULT_DASHBOARD_TIMEZONE
        return fallback, ZoneInfo(fallback)


@lru_cache(maxsize=1)
def _ordered_dashboard_timezone_names():
    ordered = []
    seen = set()
    try:
        discovered = sorted(available_timezones())
    except Exception:
        discovered = []
    for name in list(PREFERRED_DASHBOARD_TIMEZONES) + discovered + [_default_dashboard_timezone_name()]:
        normalized = _normalize_dashboard_timezone_name(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _local_now(tzinfo):
    return timezone.localtime(timezone.now(), tzinfo)


def _local_today(tzinfo):
    return _local_now(tzinfo).date()


def _make_aware_local(naive_value, tzinfo):
    try:
        return timezone.make_aware(naive_value, timezone=tzinfo)
    except TypeError:
        return timezone.make_aware(naive_value, tzinfo)


def _local_date_range_bounds(start_date=None, end_date=None, tzinfo=None):
    start_dt = None
    end_dt = None
    if start_date is not None:
        start_dt = _make_aware_local(datetime.combine(start_date, time.min), tzinfo)
    if end_date is not None:
        end_dt = _make_aware_local(datetime.combine(end_date + timedelta(days=1), time.min), tzinfo)
    return start_dt, end_dt


def _apply_local_date_range_filter(qs, field_name, start_date=None, end_date=None, tzinfo=None):
    start_dt, end_dt = _local_date_range_bounds(start_date=start_date, end_date=end_date, tzinfo=tzinfo)
    if start_dt is not None:
        qs = qs.filter(**{f"{field_name}__gte": start_dt})
    if end_dt is not None:
        qs = qs.filter(**{f"{field_name}__lt": end_dt})
    return qs


def _resolve_dashboard_scope_objects(user, filters=None):
    filters = filters or {}
    selected_branch_id = _pick_valid_int(filters.get("branch_id"))
    selected_org_id = _pick_valid_int(filters.get("org_id"))

    branch_obj = None
    org_obj = None

    if selected_branch_id is not None:
        branch_obj = _available_branches(user).select_related("org").filter(id=selected_branch_id).first()
        if branch_obj is not None:
            org_obj = branch_obj.org

    if org_obj is None and selected_org_id is not None:
        org_obj = _available_orgs(user).filter(id=selected_org_id).first()

    if branch_obj is None and getattr(user, "branch_id", None) and not _is_super(user):
        branch_obj = Branch.objects.select_related("org").filter(id=user.branch_id).first()
        if branch_obj is not None and org_obj is None:
            org_obj = branch_obj.org

    if org_obj is None and getattr(user, "organization_id", None) and not _is_super(user):
        org_obj = Organization.objects.filter(id=user.organization_id).first()

    return org_obj, branch_obj


def _build_dashboard_timezone_scope_options(user, org_obj, branch_obj):
    options = []
    options.append({"value": "global", "label": "GLOBAL"})
    if org_obj is not None:
        options.append({"value": "org", "label": f"ORG: {org_obj.code}"})
    if branch_obj is not None:
        options.append({"value": "branch", "label": f"BRANCH: {branch_obj.org.code}/{branch_obj.code}"})
    return options


def _resolve_dashboard_timezone_context(user, filters=None):
    org_obj, branch_obj = _resolve_dashboard_scope_objects(user, filters)
    global_profile = _latest_config_profile(ConfigScope.GLOBAL, org=None, branch=None, device=None)
    org_profile = _latest_config_profile(ConfigScope.ORG, org=org_obj, branch=None, device=None) if org_obj else None
    branch_profile = _latest_config_profile(ConfigScope.BRANCH, org=None, branch=branch_obj, device=None) if branch_obj else None

    global_name = (
        _normalize_dashboard_timezone_name((global_profile.payload or {}).get(DASHBOARD_TIMEZONE_KEY))
        if global_profile
        else None
    )
    org_name = (
        _normalize_dashboard_timezone_name((org_profile.payload or {}).get(DASHBOARD_TIMEZONE_KEY))
        if org_profile
        else None
    )
    branch_name = (
        _normalize_dashboard_timezone_name((branch_profile.payload or {}).get(DASHBOARD_TIMEZONE_KEY))
        if branch_profile
        else None
    )

    source_scope = "global"
    resolved_name = global_name or _default_dashboard_timezone_name()
    if org_name:
        source_scope = "org"
        resolved_name = org_name
    if branch_name:
        source_scope = "branch"
        resolved_name = branch_name

    active_name, active_tzinfo = _load_dashboard_tzinfo(resolved_name)
    scope_options = _build_dashboard_timezone_scope_options(user, org_obj, branch_obj)
    scope_values = {item["value"] for item in scope_options}
    if branch_obj is not None and "branch" in scope_values:
        selected_scope = "branch"
    elif org_obj is not None and "org" in scope_values:
        selected_scope = "org"
    elif "global" in scope_values:
        selected_scope = "global"
    else:
        selected_scope = scope_options[0]["value"] if scope_options else ""

    return {
        "dashboard_tz_name": active_name,
        "dashboard_tz_source_scope": source_scope,
        "dashboard_tz_source_org": org_obj,
        "dashboard_tz_source_branch": branch_obj,
        "dashboard_tz_scope_options": scope_options,
        "dashboard_tz_selected_scope": selected_scope,
        "dashboard_tz_choices": _ordered_dashboard_timezone_names(),
        "dashboard_tz_can_edit": bool(scope_options),
        "dashboard_tz_org_id": int(org_obj.id) if org_obj is not None else "",
        "dashboard_tz_branch_id": int(branch_obj.id) if branch_obj is not None else "",
        "dashboard_tzinfo": active_tzinfo,
    }


def _render_dashboard_page(request, template_name, context, tzinfo):
    with timezone.override(tzinfo):
        return render(request, template_name, context)


def _render_dashboard_partial(request, template_name, context, tzinfo):
    with timezone.override(tzinfo):
        return render_to_string(template_name, context, request=request)


def _build_dashboard_page_context(user, filters=None, **extra):
    tz_context = _resolve_dashboard_timezone_context(user, filters)
    tzinfo = tz_context["dashboard_tzinfo"]
    context = dict(extra)
    context.update(tz_context)
    return context, tzinfo


def _resolve_scope_filters(user, request):
    if request.method == "POST":
        raw_org = request.POST.get("org_id") or request.GET.get("org_id")
        raw_branch = request.POST.get("branch_id") or request.GET.get("branch_id")
    else:
        raw_org = request.GET.get("org_id")
        raw_branch = request.GET.get("branch_id")

    orgs_qs = _available_orgs(user)
    branches_qs = _available_branches(user)

    selected_org_id = _pick_valid_int(raw_org)
    selected_branch_id = _pick_valid_int(raw_branch)

    org_ids = set(orgs_qs.values_list("id", flat=True))
    if selected_org_id not in org_ids:
        selected_org_id = None

    branch_ids = set(branches_qs.values_list("id", flat=True))
    if selected_branch_id not in branch_ids:
        selected_branch_id = None

    if selected_branch_id is not None:
        branch_obj = branches_qs.filter(id=selected_branch_id).first()
        if branch_obj is None:
            selected_branch_id = None
        elif selected_org_id is not None and int(branch_obj.org_id) != int(selected_org_id):
            selected_branch_id = None
        elif selected_org_id is None and _is_super(user):
            selected_org_id = int(branch_obj.org_id)

    branch_options_qs = branches_qs
    if selected_org_id is not None:
        branch_options_qs = branch_options_qs.filter(org_id=selected_org_id)

    return {
        "org_id": selected_org_id,
        "branch_id": selected_branch_id,
        "orgs": orgs_qs,
        "branches": branch_options_qs,
    }


def _apply_org_branch_filter(qs, org_field, branch_field, filters):
    org_id = filters.get("org_id")
    branch_id = filters.get("branch_id")
    if org_id is not None:
        qs = qs.filter(**{org_field: org_id})
    if branch_id is not None:
        qs = qs.filter(**{branch_field: branch_id})
    return qs


def _query_params_from_filters(filters, extra=None):
    params = {}
    org_id = filters.get("org_id")
    branch_id = filters.get("branch_id")
    if org_id is not None:
        params["org_id"] = int(org_id)
    if branch_id is not None:
        params["branch_id"] = int(branch_id)
    if isinstance(extra, dict):
        for key, value in extra.items():
            if value is None or value == "":
                continue
            params[key] = value
    return params


def _build_sales_summary(user, tzinfo):
    sales = _scoped_sales(user)
    today = _local_today(tzinfo)
    now_local = _local_now(tzinfo)
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    today_total = _apply_local_date_range_filter(sales, "created_at", today, today, tzinfo).aggregate(v=Sum("price_total"))[
        "v"
    ] or 0
    month_total = _apply_local_date_range_filter(
        sales,
        "created_at",
        start_date=now_local.date().replace(day=1),
        end_date=next_month - timedelta(days=1),
        tzinfo=tzinfo,
    ).aggregate(v=Sum("price_total"))["v"] or 0
    sales_count = sales.count()
    return {
        "today_total": int(today_total),
        "month_total": int(month_total),
        "sales_count": int(sales_count),
    }


def _parse_date_ymd(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except Exception:
        return None


def _resolve_sales_period(request, tzinfo):
    period = str(request.GET.get("period") or "month").strip().lower()
    if period not in {"week", "month", "custom"}:
        period = "month"

    today = _local_today(tzinfo)
    if period == "week":
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == "month":
        start_date = today - timedelta(days=29)
        end_date = today
    else:
        start_date = _parse_date_ymd(request.GET.get("start_date"))
        end_date = _parse_date_ymd(request.GET.get("end_date"))
        if start_date is None or end_date is None:
            start_date = today - timedelta(days=29)
            end_date = today
            period = "month"
        if start_date > end_date:
            start_date, end_date = end_date, start_date
    return {"period": period, "start_date": start_date, "end_date": end_date}


def _apply_sales_period_filter(qs, period_info, tzinfo):
    start_date = period_info.get("start_date")
    end_date = period_info.get("end_date")
    return _apply_local_date_range_filter(qs, "created_at", start_date=start_date, end_date=end_date, tzinfo=tzinfo)


def _build_sales_chart_payload(sales_qs, tzinfo):
    rows = list(
        sales_qs.annotate(day=TruncDate("created_at", tzinfo=tzinfo))
        .values("day")
        .annotate(total=Sum("price_total"), tx_count=Count("id"))
        .order_by("day")
    )
    return {
        "labels": [str(row["day"]) for row in rows],
        "totals": [int(row.get("total") or 0) for row in rows],
        "counts": [int(row.get("tx_count") or 0) for row in rows],
    }


def _resolve_billing_month(request, tzinfo):
    return _parse_billing_month(request.GET.get("billing_month"), tzinfo)


def _parse_billing_month(value, tzinfo):
    raw = str(value or "").strip()
    today = _local_today(tzinfo)
    default_month = today.replace(day=1)
    if not raw:
        return default_month
    try:
        parsed = datetime.strptime(raw, "%Y-%m").date()
        return parsed.replace(day=1)
    except Exception:
        return default_month


def _billing_month_range(month_first, tzinfo):
    next_month = (month_first.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_last = next_month - timedelta(days=1)
    today = _local_today(tzinfo)
    end_date = month_last
    if month_first.year == today.year and month_first.month == today.month:
        end_date = today
    return month_first, end_date, month_last


def _shift_month(month_first, delta):
    year = int(month_first.year)
    month = int(month_first.month) + int(delta)
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return month_first.replace(year=year, month=month, day=1)


def _build_ai_branch_billing(sales_qs, start_date, end_date, tzinfo):
    scoped = _apply_local_date_range_filter(
        sales_qs.select_related("org", "branch"),
        "created_at",
        start_date=start_date,
        end_date=end_date,
        tzinfo=tzinfo,
    )
    branch_map = {}
    total_ai_sales = 0
    total_ai_images = 0

    for sale in scoped.iterator():
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

        total_ai_sales += 1
        total_ai_images += ai_images

        key = int(sale.branch_id or 0)
        row = branch_map.get(key)
        if row is None:
            row = {
                "org_id": int(sale.org_id or 0),
                "branch_id": int(sale.branch_id or 0),
                "org_code": getattr(sale.org, "code", "-"),
                "branch_code": getattr(sale.branch, "code", "-"),
                "branch_name": getattr(sale.branch, "name", "-"),
                "ai_sales": 0,
                "ai_images": 0,
                "billing_amount": 0,
            }
            branch_map[key] = row
        row["ai_sales"] += 1
        row["ai_images"] += ai_images

    rows = []
    for row in branch_map.values():
        row["billing_amount"] = int(round(row["ai_images"] * AI_EST_KRW_PER_IMAGE * AI_EST_SERVER_COST_MULTIPLIER))
        rows.append(row)
    rows.sort(key=lambda r: (str(r["org_code"]), str(r["branch_code"])))

    total_billing = int(round(total_ai_images * AI_EST_KRW_PER_IMAGE * AI_EST_SERVER_COST_MULTIPLIER))
    return rows, total_ai_sales, total_ai_images, total_billing


def _build_monthly_billing_rows(user, filters, billing_month, ui_text, tzinfo):
    branches_qs = _available_branches(user)
    if filters.get("org_id") is not None:
        branches_qs = branches_qs.filter(org_id=filters["org_id"])
    if filters.get("branch_id") is not None:
        branches_qs = branches_qs.filter(id=filters["branch_id"])
    branches = list(branches_qs.select_related("org"))
    branch_ids = [int(branch.id) for branch in branches]
    start_date, end_date, month_last = _billing_month_range(billing_month, tzinfo)
    server_fee_unit = int(max(0, MONTHLY_SERVER_FEE_PER_DEVICE))

    device_count_map = {}
    if branch_ids:
        device_count_rows = (
            Device.objects.filter(branch_id__in=branch_ids, is_active=True)
            .values("branch_id")
            .annotate(total=Count("id"))
        )
        device_count_map = {
            int(row["branch_id"]): int(row.get("total") or 0)
            for row in device_count_rows
        }

    sales_qs = _apply_org_branch_filter(_scoped_sales(user), "org_id", "branch_id", filters)
    ai_branch_rows, _ai_sales_count, _ai_images_count, _ai_total = _build_ai_branch_billing(
        sales_qs,
        start_date,
        end_date,
        tzinfo,
    )
    ai_map = {
        int(row.get("branch_id") or 0): dict(row)
        for row in ai_branch_rows
    }

    record_map = {}
    if branch_ids:
        record_qs = BranchMonthlyBilling.objects.filter(
            branch_id__in=branch_ids,
            billing_month=billing_month,
        ).select_related("updated_by")
        record_map = {int(record.branch_id): record for record in record_qs}

    rows = []
    billing_text = ui_text["billing"]
    summary = {
        "branch_count": 0,
        "device_count": 0,
        "server_fee_total": 0,
        "ai_extra_total": 0,
        "requested_total": 0,
        "paid_count": 0,
    }
    for branch in branches:
        device_count = int(device_count_map.get(int(branch.id), 0))
        ai_row = ai_map.get(int(branch.id), {})
        server_fee = int(device_count * server_fee_unit)
        ai_extra = int(ai_row.get("billing_amount") or 0)
        requested_total = int(server_fee + ai_extra)
        record = record_map.get(int(branch.id))
        status = record.status if record else BranchMonthlyBilling.STATUS_PENDING
        row = {
            "org": branch.org,
            "branch": branch,
            "device_count": device_count,
            "server_fee": server_fee,
            "server_fee_display": format_dashboard_amount(server_fee),
            "ai_sales": int(ai_row.get("ai_sales") or 0),
            "ai_images": int(ai_row.get("ai_images") or 0),
            "ai_extra": ai_extra,
            "ai_extra_display": format_dashboard_amount(ai_extra),
            "requested_total": requested_total,
            "requested_total_display": format_dashboard_amount(requested_total),
            "status": status,
            "status_label": (
                billing_text["status_paid"]
                if status == BranchMonthlyBilling.STATUS_PAID
                else billing_text["status_pending"]
            ),
            "paid_at": getattr(record, "paid_at", None),
            "note": getattr(record, "note", "") if record else "",
            "updated_by": getattr(record, "updated_by", None) if record else None,
        }
        rows.append(row)
        summary["branch_count"] += 1
        summary["device_count"] += device_count
        summary["server_fee_total"] += server_fee
        summary["ai_extra_total"] += ai_extra
        summary["requested_total"] += requested_total
        if status == BranchMonthlyBilling.STATUS_PAID:
            summary["paid_count"] += 1

    return {
        "rows": rows,
        "summary": summary,
        "summary_display": {
            "server_fee_total": format_dashboard_amount(summary["server_fee_total"]),
            "ai_extra_total": format_dashboard_amount(summary["ai_extra_total"]),
            "requested_total": format_dashboard_amount(summary["requested_total"]),
        },
        "start_date": start_date,
        "end_date": end_date,
        "month_last": month_last,
        "server_fee_unit": server_fee_unit,
        "server_fee_unit_display": format_dashboard_amount(server_fee_unit),
    }


def _build_ops_dashboard(user, filters, tzinfo):
    devices_qs = _apply_org_branch_filter(_scoped_devices(user), "org_id", "branch_id", filters)
    device_rows = _build_device_rows(user, devices_qs=devices_qs)
    device_ids = [int(row["device"].id) for row in device_rows]
    now = timezone.now()
    since_1h = now - timedelta(hours=1)
    since_24h = now - timedelta(hours=24)

    for row in device_rows:
        health = row["device"].last_health_json if isinstance(row["device"].last_health_json, dict) else {}
        row["offline_queue_total"] = int(health.get("offline_queue_total") or 0)
        row["offline_queue_sale_pending"] = int(health.get("offline_queue_sale_pending") or 0)
        row["offline_queue_share_pending"] = int(health.get("offline_queue_share_pending") or 0)
        row["offline_queue_heartbeat_pending"] = int(health.get("offline_queue_heartbeat_pending") or 0)

    heartbeat_qs = DeviceHeartbeat.objects.filter(device_id__in=device_ids) if device_ids else DeviceHeartbeat.objects.none()
    share_qs = ShareSession.objects.filter(device_id__in=device_ids) if device_ids else ShareSession.objects.none()
    upload_qs = UploadAsset.objects.filter(device_id__in=device_ids) if device_ids else UploadAsset.objects.none()
    sales_qs = SaleTransaction.objects.filter(device_id__in=device_ids) if device_ids else SaleTransaction.objects.none()

    recent_share_rows = []
    recent_shares = list(
        share_qs.select_related("device", "device__org", "device__branch").order_by("-created_at")[:20]
    )
    upload_count_map = {}
    if recent_shares:
        share_ids = [int(share.id) for share in recent_shares]
        upload_count_rows = (
            UploadAsset.objects.filter(share_id__in=share_ids)
            .values("share_id")
            .annotate(total=Count("id"))
        )
        upload_count_map = {
            int(row["share_id"]): int(row.get("total") or 0)
            for row in upload_count_rows
        }
    for share in recent_shares:
        recent_share_rows.append(
            {
                "share": share,
                "upload_count": int(upload_count_map.get(int(share.id), 0)),
                "file_keys": sorted((share.files or {}).keys()) if isinstance(share.files, dict) else [],
            }
        )

    summary = {
        "device_count": len(device_rows),
        "online_count": sum(1 for row in device_rows if row.get("online")),
        "locked_count": sum(1 for row in device_rows if row.get("server_lock_active")),
        "share_queue_device_count": sum(1 for row in device_rows if int(row.get("offline_queue_share_pending") or 0) > 0),
        "heartbeat_1h": int(heartbeat_qs.filter(created_at__gte=since_1h).count()),
        "heartbeat_24h": int(heartbeat_qs.filter(created_at__gte=since_24h).count()),
        "share_24h": int(share_qs.filter(created_at__gte=since_24h).count()),
        "share_finalized_24h": int(
            share_qs.filter(created_at__gte=since_24h, status=ShareSession.STATUS_FINALIZED).count()
        ),
        "upload_24h": int(upload_qs.filter(created_at__gte=since_24h).count()),
        "sales_24h": int(sales_qs.filter(created_at__gte=since_24h).count()),
    }
    return {
        "summary": summary,
        "device_rows": device_rows,
        "recent_share_rows": recent_share_rows,
        "generated_at": timezone.localtime(now, tzinfo),
    }


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


def _build_device_rows(user, only_locked=False, devices_qs=None):
    devices_qs = devices_qs if devices_qs is not None else _scoped_devices(user)
    devices = list(devices_qs[:300])
    device_ids = [int(d.id) for d in devices]
    default_capacity = 400
    try:
        default_capacity = max(0, int(getattr(settings, "DASHBOARD_FILM_DEFAULT_CAPACITY", 400)))
    except Exception:
        default_capacity = 400
    usage_map = {}
    if device_ids:
        usage_rows = (
            SaleTransaction.objects.filter(device_id__in=device_ids)
            .values("device_id")
            .annotate(total_prints=Sum("prints"))
        )
        usage_map = {int(row["device_id"]): int(row.get("total_prints") or 0) for row in usage_rows}

    now = timezone.now()
    threshold = int(getattr(settings, "OFFLINE_THRESHOLD_SECONDS", 120))
    rows = []
    for d in devices:
        health = d.last_health_json if isinstance(d.last_health_json, dict) else {}
        online = bool(d.last_seen_at and (now - d.last_seen_at).total_seconds() < threshold)
        film_remaining = _extract_film_remaining(health)
        film_estimated = False
        if film_remaining is None:
            used = max(0, int(usage_map.get(int(d.id), 0)))
            film_remaining = max(0, int(default_capacity) - used)
            film_estimated = True
        rows.append(
            {
                "device": d,
                "online": online,
                "internet_ok": health.get("internet_ok"),
                "camera_ok": health.get("camera_ok"),
                "printer_ok": _derive_printer_ok(health),
                "film_remaining": film_remaining,
                "film_remaining_estimated": film_estimated,
                "offline_guard_enabled": bool(health.get("offline_guard_enabled", False)),
                "offline_lock_active": bool(health.get("offline_lock_active", False)),
                "offline_grace_remaining_seconds": _as_optional_int(health.get("offline_grace_remaining_seconds")),
                "offline_last_online_at": health.get("offline_last_online_at"),
                "server_lock_active": bool(d.is_locked),
                "server_lock_reason": d.lock_reason or "",
                "server_locked_at": d.locked_at,
                "allow_celebrity_mode": bool(getattr(d, "allow_celebrity_mode", True)),
                "allow_ai_mode": bool(getattr(d, "allow_ai_mode", True)),
            }
        )
    for row in rows:
        remain = row.get("offline_grace_remaining_seconds")
        if remain is None:
            row["offline_grace_text"] = "-"
            row["offline_grace_overdue"] = False
            continue
        remain_int = int(remain)
        if remain_int >= 0:
            row["offline_grace_text"] = _format_duration_compact(remain_int)
            row["offline_grace_overdue"] = False
        else:
            row["offline_grace_text"] = f"초과 {_format_duration_compact(abs(remain_int))}"
            row["offline_grace_overdue"] = True
    for row in rows:
        row["locked_any"] = bool(row.get("offline_lock_active") or row.get("server_lock_active"))
    if only_locked:
        rows = [row for row in rows if row.get("locked_any")]
    return rows


def _save_dashboard_timezone_profile(user, scope_value, timezone_name, org_id=None, branch_id=None):
    normalized_name = _normalize_dashboard_timezone_name(timezone_name)
    if not normalized_name:
        raise ValueError("유효한 시간대를 선택하세요.")

    scope_value = str(scope_value or "").strip().lower()
    target_scope = None
    target_org = None
    target_branch = None
    available_orgs = _available_orgs(user)
    available_branches = _available_branches(user)

    if scope_value == "global":
        target_scope = ConfigScope.GLOBAL
    elif scope_value == "org":
        target_org = available_orgs.filter(id=_pick_valid_int(org_id)).first()
        if target_org is None and getattr(user, "organization_id", None):
            target_org = available_orgs.filter(id=user.organization_id).first()
        if target_org is None and getattr(user, "branch_id", None):
            branch_obj = available_branches.select_related("org").filter(id=user.branch_id).first()
            if branch_obj is not None:
                target_org = branch_obj.org
        if target_org is None:
            raise ValueError("적용할 조직을 찾을 수 없습니다.")
        target_scope = ConfigScope.ORG
    elif scope_value == "branch":
        branch_pk = _pick_valid_int(branch_id)
        target_branch = available_branches.select_related("org").filter(id=branch_pk).first()
        if target_branch is None and getattr(user, "branch_id", None):
            target_branch = available_branches.select_related("org").filter(id=user.branch_id).first()
        if target_branch is None:
            raise ValueError("적용할 지점을 찾을 수 없습니다.")
        target_scope = ConfigScope.BRANCH
    else:
        raise ValueError("지원하지 않는 시간대 범위입니다.")

    latest = _latest_config_profile(
        target_scope,
        org=target_org if target_scope == ConfigScope.ORG else None,
        branch=target_branch if target_scope == ConfigScope.BRANCH else None,
        device=None,
    )
    payload = dict(latest.payload or {}) if latest else {}
    payload[DASHBOARD_TIMEZONE_KEY] = normalized_name
    ConfigProfile.objects.create(
        scope=target_scope,
        org=target_org if target_scope == ConfigScope.ORG else None,
        branch=target_branch if target_scope == ConfigScope.BRANCH else None,
        device=None,
        payload=payload,
        updated_by=user,
    )

    if target_scope == ConfigScope.GLOBAL:
        return f"전역 기준 시간이 {normalized_name}로 저장되었습니다."
    if target_scope == ConfigScope.ORG:
        return f"{target_org.code} 조직 기준 시간이 {normalized_name}로 저장되었습니다."
    return f"{target_branch.org.code}/{target_branch.code} 지점 기준 시간이 {normalized_name}로 저장되었습니다."


@never_cache
def login_view(request):
    ui_lang = resolve_dashboard_lang(request)
    if request.user.is_authenticated:
        return redirect(f"/dashboard/?{urlencode({'lang': ui_lang})}")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "dashboard_index")
    return render(request, "dashboard/login.html", {"form": form})


@never_cache
def logout_view(request):
    if request.method not in {"GET", "POST"}:
        return HttpResponseNotAllowed(["GET", "POST"])
    ui_lang = resolve_dashboard_lang(request)
    logout(request)
    response = redirect(f"/dashboard/login?{urlencode({'lang': ui_lang})}")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["Clear-Site-Data"] = '"cache", "cookies", "storage"'
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path=getattr(settings, "SESSION_COOKIE_PATH", "/"),
        domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "SESSION_COOKIE_SAMESITE", None),
    )
    response.delete_cookie(
        settings.CSRF_COOKIE_NAME,
        path=getattr(settings, "CSRF_COOKIE_PATH", "/"),
        domain=getattr(settings, "CSRF_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "CSRF_COOKIE_SAMESITE", None),
    )
    return response


@login_required(login_url="/dashboard/login")
@never_cache
def currency_unit_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    resolve_dashboard_currency_unit(request)
    next_url = str(request.POST.get("next") or "").strip()
    if not next_url.startswith("/dashboard"):
        next_url = "/dashboard/"
    return redirect(next_url)


@login_required(login_url="/dashboard/login")
@never_cache
def dashboard_timezone_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    next_url = str(request.POST.get("next") or "").strip()
    if not next_url.startswith("/dashboard"):
        next_url = "/dashboard/"
    try:
        message = _save_dashboard_timezone_profile(
            request.user,
            scope_value=request.POST.get("timezone_scope"),
            timezone_name=request.POST.get("timezone_name"),
            org_id=request.POST.get("org_id"),
            branch_id=request.POST.get("branch_id"),
        )
    except PermissionError as exc:
        return HttpResponseForbidden(str(exc))
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect(next_url)

    messages.success(request, message)
    return redirect(next_url)


@login_required(login_url="/dashboard/login")
@never_cache
def index_view(request):
    context, tzinfo = _build_dashboard_page_context(request.user)
    summary = _build_sales_summary(request.user, tzinfo)
    context.update(
        {
            "today_total": summary["today_total"],
            "month_total": summary["month_total"],
            "sales_count": summary["sales_count"],
            "can_edit": not _is_viewer(request.user),
        }
    )
    return _render_dashboard_page(request, "dashboard/index.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def index_live_view(request):
    tz_context = _resolve_dashboard_timezone_context(request.user)
    tzinfo = tz_context["dashboard_tzinfo"]
    summary = _build_sales_summary(request.user, tzinfo)
    summary["ok"] = True
    summary["generated_at"] = timezone.localtime(timezone.now(), tzinfo).strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse(summary)


@login_required(login_url="/dashboard/login")
@never_cache
def devices_view(request):
    user = request.user
    filters = _resolve_scope_filters(user, request)
    context, tzinfo = _build_dashboard_page_context(user, filters)
    can_edit_notifications = not _is_viewer(user)
    can_manage_locks = not _is_viewer(user)
    only_locked = str(request.GET.get("locked", "")).strip() == "1"

    if request.method == "POST":
        if not can_edit_notifications:
            return HttpResponseForbidden("Viewer is read-only")
        action = (request.POST.get("action") or "").strip()
        if action == "save_alert_emails":
            emails = _parse_email_list(request.POST.get("alert_emails", ""))
            scope_org = _notification_scope_org(user)
            existing = _get_scope_email_channels(user)
            existing.delete()
            created = 0
            for email in emails:
                NotificationChannel.objects.create(
                    org=scope_org,
                    type=ChannelType.EMAIL,
                    enabled=True,
                    config={"to": email},
                )
                created += 1
            messages.success(request, f"알림 이메일 저장 완료: {created}개")
        elif action == "send_test_email":
            targets = _get_scope_email_targets(user)
            if not targets:
                messages.error(request, "먼저 알림 이메일을 저장하세요.")
                return redirect("dashboard_devices")
            backend = str(getattr(settings, "EMAIL_BACKEND", "") or "")
            if "console.EmailBackend" in backend:
                messages.warning(
                    request,
                    "현재 이메일 백엔드가 콘솔 모드입니다. 실제 메일 발송을 위해 SMTP 설정을 먼저 입력하세요.",
                )
                return redirect("dashboard_devices")
            now_local = timezone.localtime(timezone.now(), tzinfo).strftime("%Y-%m-%d %H:%M:%S")
            subject = "[Viorafilm] 테스트 알림 메일"
            body = (
                "이 메일은 Viorafilm 대시보드에서 발송한 테스트 알림입니다.\n"
                f"시간: {now_local}\n"
                f"발신 사용자: {user.username}\n"
            )
            sent, failed = send_email_targets(targets, subject, body)
            if sent:
                messages.success(request, f"테스트 메일 발송 완료: 성공 {sent}, 실패 {failed}")
            else:
                messages.error(request, f"테스트 메일 발송 실패: 성공 {sent}, 실패 {failed}")
        elif action in ("lock_device", "unlock_device"):
            device_id_raw = (request.POST.get("device_id") or "").strip()
            if not device_id_raw.isdigit():
                messages.error(request, "잘못된 장치 ID 입니다.")
                return redirect("dashboard_devices")

            target = _scoped_devices(user).filter(id=int(device_id_raw)).first()
            if not target:
                messages.error(request, "해당 장치를 찾을 수 없습니다.")
                return redirect("dashboard_devices")
            if not can_manage_locks:
                return HttpResponseForbidden("Viewer is read-only")

            if action == "lock_device":
                reason = (request.POST.get("lock_reason") or "").strip()
                target.is_locked = True
                target.lock_reason = reason[:255]
                target.locked_at = timezone.now()
                target.save(update_fields=["is_locked", "lock_reason", "locked_at", "updated_at"])
                log_event(
                    actor_user=user,
                    actor_device=None,
                    action="device.lock",
                    target_type="Device",
                    target_id=str(target.id),
                    before=None,
                    after={"device_code": target.device_code, "lock_reason": target.lock_reason},
                    meta={},
                    ip=request.META.get("REMOTE_ADDR"),
                )
                messages.success(request, f"장치 잠금 처리 완료: {target.device_code}")
            else:
                old_reason = target.lock_reason
                target.is_locked = False
                target.lock_reason = ""
                target.locked_at = None
                target.save(update_fields=["is_locked", "lock_reason", "locked_at", "updated_at"])
                log_event(
                    actor_user=user,
                    actor_device=None,
                    action="device.unlock",
                    target_type="Device",
                    target_id=str(target.id),
                    before={"lock_reason": old_reason},
                    after={"device_code": target.device_code},
                    meta={},
                    ip=request.META.get("REMOTE_ADDR"),
                )
                messages.success(request, f"장치 잠금 해제 완료: {target.device_code}")
        params = _query_params_from_filters(filters, extra={"locked": "1" if only_locked else None})
        if params:
            return redirect(f"/dashboard/devices?{urlencode(params)}")
        return redirect("dashboard_devices")

    filtered_devices = _apply_org_branch_filter(_scoped_devices(user), "org_id", "branch_id", filters)
    rows = _build_device_rows(user, only_locked=only_locked, devices_qs=filtered_devices)

    context.update(
        {
            "rows": rows,
            "only_locked": only_locked,
            "can_edit_notifications": can_edit_notifications,
            "can_manage_locks": can_manage_locks,
            "alert_emails_text": ", ".join(_get_scope_email_targets(user)),
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/devices.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def devices_live_view(request):
    user = request.user
    filters = _resolve_scope_filters(user, request)
    tz_context = _resolve_dashboard_timezone_context(user, filters)
    tzinfo = tz_context["dashboard_tzinfo"]
    only_locked = str(request.GET.get("locked", "")).strip() == "1"
    filtered_devices = _apply_org_branch_filter(_scoped_devices(user), "org_id", "branch_id", filters)
    rows = _build_device_rows(user, only_locked=only_locked, devices_qs=filtered_devices)
    can_manage_locks = not _is_viewer(user)
    tbody_html = _render_dashboard_partial(
        request,
        "dashboard/_devices_tbody.html",
        {
            "rows": rows,
            "can_manage_locks": can_manage_locks,
        },
        tzinfo,
    )
    return JsonResponse(
        {
            "ok": True,
            "generated_at": timezone.localtime(timezone.now(), tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(rows),
            "tbody_html": tbody_html,
        }
    )


@login_required(login_url="/dashboard/login")
@never_cache
def billing_view(request):
    user = request.user
    if not _can_manage_billing(user):
        return HttpResponseForbidden("Billing is available only for admin")
    ui_lang = resolve_dashboard_lang(request)
    ui_text = get_dashboard_text(ui_lang)
    billing_text = ui_text["billing"]
    filters = _resolve_scope_filters(user, request)
    context, tzinfo = _build_dashboard_page_context(user, filters)
    billing_month = _parse_billing_month(
        request.POST.get("billing_month") if request.method == "POST" else request.GET.get("billing_month"),
        tzinfo,
    )
    can_edit = not _is_viewer(user)

    scoped_branches = _available_branches(user)
    if filters.get("org_id") is not None:
        scoped_branches = scoped_branches.filter(org_id=filters["org_id"])
    if filters.get("branch_id") is not None:
        scoped_branches = scoped_branches.filter(id=filters["branch_id"])

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Viewer is read-only")
        action = str(request.POST.get("action") or "").strip()
        try:
            branch_id = int(request.POST.get("branch_id") or 0)
        except Exception:
            branch_id = 0
        note = str(request.POST.get("note") or "").strip()[:255]
        branch = scoped_branches.select_related("org").filter(id=branch_id).first()
        if branch is None:
            messages.error(request, billing_text["message_missing_branch"])
        elif action in {"mark_paid", "mark_pending"}:
            record, _created = BranchMonthlyBilling.objects.get_or_create(
                org=branch.org,
                branch=branch,
                billing_month=billing_month,
            )
            before = {
                "status": record.status,
                "paid_at": record.paid_at.isoformat() if record.paid_at else None,
                "note": record.note,
            }
            if action == "mark_paid":
                record.status = BranchMonthlyBilling.STATUS_PAID
                record.paid_at = timezone.now()
                messages.success(
                    request,
                    billing_text["message_paid"].format(branch=branch.name, month=billing_month.strftime("%Y-%m")),
                )
            else:
                record.status = BranchMonthlyBilling.STATUS_PENDING
                record.paid_at = None
                messages.success(
                    request,
                    billing_text["message_pending"].format(branch=branch.name, month=billing_month.strftime("%Y-%m")),
                )
            record.note = note
            record.updated_by = user
            record.save()
            log_event(
                actor_user=user,
                actor_device=None,
                action="billing.update",
                target_type="BranchMonthlyBilling",
                target_id=str(record.pk),
                before=before,
                after={
                    "status": record.status,
                    "paid_at": record.paid_at.isoformat() if record.paid_at else None,
                    "note": record.note,
                },
                meta={
                    "branch_id": int(branch.id),
                    "billing_month": billing_month.isoformat(),
                },
                ip=request.META.get("REMOTE_ADDR"),
            )
        else:
            messages.error(request, billing_text["message_unsupported"])
        params = _query_params_from_filters(
            filters,
            extra={
                "billing_month": billing_month.strftime("%Y-%m"),
                "lang": ui_lang,
            },
        )
        if params:
            return redirect(f"/dashboard/billing?{urlencode(params)}")
        return redirect("dashboard_billing")

    billing_data = _build_monthly_billing_rows(user, filters, billing_month, ui_text, tzinfo)
    prev_month = _shift_month(billing_month, -1)
    next_month = _shift_month(billing_month, 1)
    billing_nav_base = _query_params_from_filters(
        filters,
        extra={
            "lang": ui_lang,
        },
    )
    prev_month_params = dict(billing_nav_base)
    prev_month_params["billing_month"] = prev_month.strftime("%Y-%m")
    next_month_params = dict(billing_nav_base)
    next_month_params["billing_month"] = next_month.strftime("%Y-%m")
    context.update(
        {
            "billing_text": billing_text,
            "billing_month_value": billing_month.strftime("%Y-%m"),
            "billing_start_date": billing_data["start_date"].isoformat(),
            "billing_end_date": billing_data["end_date"].isoformat(),
            "billing_month_last": billing_data["month_last"].isoformat(),
            "billing_rows": billing_data["rows"],
            "billing_summary": billing_data["summary"],
            "billing_summary_display": billing_data["summary_display"],
            "server_fee_unit": billing_data["server_fee_unit"],
            "server_fee_unit_display": billing_data["server_fee_unit_display"],
            "billing_prev_month_value": prev_month.strftime("%Y-%m"),
            "billing_next_month_value": next_month.strftime("%Y-%m"),
            "billing_prev_month_url": f"/dashboard/billing?{urlencode(prev_month_params)}",
            "billing_next_month_url": f"/dashboard/billing?{urlencode(next_month_params)}",
            "ui_lang": ui_lang,
            "can_edit": can_edit,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/billing.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def ops_view(request):
    filters = _resolve_scope_filters(request.user, request)
    context, tzinfo = _build_dashboard_page_context(request.user, filters)
    ops_data = _build_ops_dashboard(request.user, filters, tzinfo)
    context.update(
        {
            "ops_summary": ops_data["summary"],
            "ops_device_rows": ops_data["device_rows"],
            "ops_recent_share_rows": ops_data["recent_share_rows"],
            "ops_generated_at": ops_data["generated_at"],
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/ops.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def sales_view(request):
    filters = _resolve_scope_filters(request.user, request)
    context, tzinfo = _build_dashboard_page_context(request.user, filters)
    period_info = _resolve_sales_period(request, tzinfo)
    sales_base_qs = _apply_org_branch_filter(_scoped_sales(request.user), "org_id", "branch_id", filters)
    sales_qs = _apply_sales_period_filter(sales_base_qs, period_info, tzinfo)
    sales = list(sales_qs[:300])
    total_amount = int(sales_qs.aggregate(v=Sum("price_total")).get("v") or 0)
    total_count = int(sales_qs.count())

    mode_counts = {"normal": 0, "ai": 0, "celebrity": 0}
    mode_amounts = {"normal": 0, "ai": 0, "celebrity": 0}
    ai_generated_images = 0
    for price_total, meta in sales_qs.values_list("price_total", "meta"):
        mode = "normal"
        sale_ai_images = 0
        if isinstance(meta, dict):
            raw_mode = str(meta.get("compose_mode", "")).strip().lower()
            if raw_mode in {"ai", "celebrity"}:
                mode = raw_mode
            if mode == "ai":
                try:
                    sale_ai_images = int(meta.get("ai_generated_count", AI_EST_DEFAULT_IMAGES_PER_SALE) or 0)
                except Exception:
                    sale_ai_images = AI_EST_DEFAULT_IMAGES_PER_SALE
                if sale_ai_images <= 0:
                    sale_ai_images = AI_EST_DEFAULT_IMAGES_PER_SALE
        amount = int(price_total or 0)
        mode_counts[mode] += 1
        mode_amounts[mode] += amount
        if mode == "ai":
            ai_generated_images += sale_ai_images

    billing_month = _resolve_billing_month(request, tzinfo)
    billing_start_date, billing_end_date, billing_month_last = _billing_month_range(billing_month, tzinfo)
    ai_branch_rows, ai_branch_sales_count, ai_branch_images_count, ai_branch_billing_total = _build_ai_branch_billing(
        sales_base_qs,
        billing_start_date,
        billing_end_date,
        tzinfo,
    )

    chart_payload = _build_sales_chart_payload(sales_qs, tzinfo)
    context.update(
        {
            "sales": sales,
            "sales_total_amount": total_amount,
            "sales_total_count": total_count,
            "period": period_info["period"],
            "start_date": period_info["start_date"].isoformat() if period_info["start_date"] else "",
            "end_date": period_info["end_date"].isoformat() if period_info["end_date"] else "",
            "chart_labels": chart_payload["labels"],
            "chart_totals": chart_payload["totals"],
            "chart_counts": chart_payload["counts"],
            "mode_counts": mode_counts,
            "mode_amounts": mode_amounts,
            "ai_generated_images": ai_generated_images,
            "billing_month_value": billing_month.strftime("%Y-%m"),
            "billing_start_date": billing_start_date.isoformat(),
            "billing_end_date": billing_end_date.isoformat(),
            "billing_month_last": billing_month_last.isoformat(),
            "ai_branch_rows": ai_branch_rows,
            "ai_branch_sales_count": ai_branch_sales_count,
            "ai_branch_images_count": ai_branch_images_count,
            "ai_branch_billing_total": ai_branch_billing_total,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/sales.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def sales_export_view(request):
    filters = _resolve_scope_filters(request.user, request)
    tz_context = _resolve_dashboard_timezone_context(request.user, filters)
    tzinfo = tz_context["dashboard_tzinfo"]
    period_info = _resolve_sales_period(request, tzinfo)
    sales_qs = _apply_org_branch_filter(_scoped_sales(request.user), "org_id", "branch_id", filters)
    sales_qs = _apply_sales_period_filter(sales_qs, period_info, tzinfo)

    rows = []
    for s in sales_qs.order_by("-created_at").iterator():
        meta = s.meta if isinstance(s.meta, dict) else {}
        compose_mode = str(meta.get("compose_mode", "normal")).strip().lower() or "normal"
        if compose_mode not in {"normal", "ai", "celebrity"}:
            compose_mode = "normal"
        rows.append(
            [
                timezone.localtime(s.created_at, tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
                getattr(s.org, "code", ""),
                getattr(s.branch, "code", ""),
                getattr(s.device, "device_code", ""),
                s.session_id,
                s.layout_id,
                s.prints,
                s.currency,
                s.price_total,
                s.payment_method,
                s.amount_cash,
                s.amount_coupon,
                s.coupon.formatted_code if s.coupon else "",
                compose_mode,
            ]
        )

    filename = f"viorafilm_sales_{timezone.localtime(timezone.now(), tzinfo).strftime('%Y%m%d_%H%M%S')}.csv"
    return _csv_response(
        filename=filename,
        headers=[
            "created_at",
            "org_code",
            "branch_code",
            "device_code",
            "session_id",
            "layout_id",
            "prints",
            "currency",
            "price_total",
            "payment_method",
            "amount_cash",
            "amount_coupon",
            "coupon_code",
            "compose_mode",
        ],
        rows=rows,
    )


@login_required(login_url="/dashboard/login")
@never_cache
def coupons_view(request):
    user = request.user
    filters = _resolve_scope_filters(user, request)
    context, tzinfo = _build_dashboard_page_context(user, filters)
    can_edit = not _is_viewer(user)
    coupons = _apply_org_branch_filter(
        _scoped_coupons(user),
        "batch__org_id",
        "batch__branch_id",
        filters,
    )
    global_coupon_total_count = int(Coupon.objects.count())
    scoped_coupon_total_count = int(coupons.count())
    coupon_global_capacity_visible = _is_super(user)
    coupon_total_count = global_coupon_total_count if coupon_global_capacity_visible else scoped_coupon_total_count
    coupon_remaining_capacity = (
        max(0, int(MAX_TOTAL_COUPONS - global_coupon_total_count))
        if coupon_global_capacity_visible
        else None
    )
    per_page_raw = request.GET.get("per_page") or request.POST.get("per_page") or 30
    try:
        per_page = int(per_page_raw)
    except Exception:
        per_page = 30
    if per_page not in COUPON_PER_PAGE_OPTIONS:
        per_page = 30
    page_raw = request.GET.get("page") or request.POST.get("page") or 1
    try:
        current_page = int(page_raw)
    except Exception:
        current_page = 1

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Viewer is read-only")
        action = (request.POST.get("action") or "").strip()

        if action == "issue":
            try:
                amount = int(request.POST.get("amount") or 0)
            except Exception:
                amount = 0
            try:
                count = int(request.POST.get("count") or 0)
            except Exception:
                count = 0
            title = (request.POST.get("title") or "").strip()
            expires_period = (request.POST.get("expires_period") or "1d").strip().lower()
            expires_hours = resolve_expires_hours(expires_period=expires_period, expires_hours=24)
            org_id = request.POST.get("org_id")
            branch_id = request.POST.get("branch_id")

            if _is_super(user):
                org = Organization.objects.filter(id=org_id).first() if org_id else None
                branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
            elif _is_org_admin(user):
                org = user.organization
                branch = Branch.objects.filter(id=branch_id, org=org).first() if branch_id else None
            else:
                org = user.organization
                branch = user.branch

            if amount <= 0 or count <= 0 or expires_hours <= 0:
                messages.error(request, "amount/count/expires_hours must be > 0")
            else:
                try:
                    batch = create_batch_and_coupons(
                        org=org,
                        branch=branch,
                        amount=amount,
                        count=count,
                        expires_hours=expires_hours,
                        created_by=user,
                        title=title,
                    )
                    messages.success(request, f"쿠폰 묶음 발행 완료 (Batch #{batch.id})")
                except ValueError as exc:
                    messages.error(request, str(exc))

        elif action == "delete_selected":
            ids = [int(x) for x in request.POST.getlist("coupon_ids") if str(x).isdigit()]
            targets = coupons.filter(id__in=ids)
            count = targets.count()
            before_ids = list(targets.values_list("id", flat=True))
            targets.delete()
            if count:
                log_event(
                    actor_user=user,
                    actor_device=None,
                    action="coupon.delete",
                    target_type="Coupon",
                    target_id="bulk-selected",
                    before={"coupon_ids": before_ids},
                    after={"deleted": count},
                    meta={"action": action},
                    ip=request.META.get("REMOTE_ADDR"),
                )
            messages.success(request, f"Deleted selected coupons: {count}")

        elif action == "delete_used":
            targets = coupons.filter(used_at__isnull=False)
            count = targets.count()
            before_ids = list(targets.values_list("id", flat=True))
            targets.delete()
            if count:
                log_event(
                    actor_user=user,
                    actor_device=None,
                    action="coupon.delete",
                    target_type="Coupon",
                    target_id="bulk-used",
                    before={"coupon_ids": before_ids},
                    after={"deleted": count},
                    meta={"action": action},
                    ip=request.META.get("REMOTE_ADDR"),
                )
            messages.success(request, f"Deleted used coupons: {count}")

        elif action == "delete_expired":
            targets = coupons.filter(expires_at__lte=timezone.now(), used_at__isnull=True)
            count = targets.count()
            before_ids = list(targets.values_list("id", flat=True))
            targets.delete()
            if count:
                log_event(
                    actor_user=user,
                    actor_device=None,
                    action="coupon.delete",
                    target_type="Coupon",
                    target_id="bulk-expired",
                    before={"coupon_ids": before_ids},
                    after={"deleted": count},
                    meta={"action": action},
                    ip=request.META.get("REMOTE_ADDR"),
                )
            messages.success(request, f"Deleted expired coupons: {count}")
        elif action == "recover_missing_usage":
            stats = recover_coupon_usage_from_sales(
                actor_user=user,
                org_id=filters.get("org_id"),
                branch_id=filters.get("branch_id"),
                ip=request.META.get("REMOTE_ADDR"),
            )
            messages.success(
                request,
                "누락 사용 복구 완료 "
                f"(검사 {stats['scanned']} / 연결 {stats['linked_sales']} / 사용처리 {stats['coupon_marked_used']} / "
                f"코드없음 {stats['skipped_no_code']} / 미존재 {stats['skipped_not_found']} / 충돌 {stats['skipped_conflict']})",
            )

        params = _query_params_from_filters(
            filters,
            extra={
                "per_page": per_page,
                "page": current_page,
            },
        )
        if params:
            return redirect(f"/dashboard/coupons?{urlencode(params)}")
        return redirect("dashboard_coupons")

    paginator = Paginator(coupons, per_page)
    page_obj = paginator.get_page(current_page)
    page_numbers = [
        num
        for num in range(max(1, page_obj.number - 2), min(paginator.num_pages, page_obj.number + 2) + 1)
    ]

    context.update(
        {
            "coupons": page_obj.object_list,
            "page_obj": page_obj,
            "page_numbers": page_numbers,
            "per_page": per_page,
            "per_page_options": COUPON_PER_PAGE_OPTIONS,
            "orgs": _available_orgs(user),
            "branches": _available_branches(user),
            "can_edit": can_edit,
            "coupon_total_count": coupon_total_count,
            "coupon_remaining_capacity": coupon_remaining_capacity,
            "coupon_max_total": int(MAX_TOTAL_COUPONS),
            "coupon_max_per_issue": int(MAX_COUPON_BATCH_COUNT),
            "coupon_global_capacity_visible": coupon_global_capacity_visible,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/coupons.html", context, tzinfo)


@login_required(login_url="/dashboard/login")
@never_cache
def coupons_export_view(request):
    filters = _resolve_scope_filters(request.user, request)
    tz_context = _resolve_dashboard_timezone_context(request.user, filters)
    tzinfo = tz_context["dashboard_tzinfo"]
    coupons_qs = _apply_org_branch_filter(
        _scoped_coupons(request.user),
        "batch__org_id",
        "batch__branch_id",
        filters,
    ).order_by("-created_at")

    rows = []
    for c in coupons_qs.iterator():
        rows.append(
            [
                c.formatted_code,
                c.code,
                c.currency,
                c.amount,
                c.status,
                timezone.localtime(c.created_at, tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
                timezone.localtime(c.expires_at, tzinfo).strftime("%Y-%m-%d %H:%M:%S"),
                timezone.localtime(c.used_at, tzinfo).strftime("%Y-%m-%d %H:%M:%S") if c.used_at else "",
                getattr(c.batch.org, "code", "") if c.batch else "",
                getattr(c.batch.branch, "code", "") if c.batch else "",
                c.used_session_id or "",
                c.used_by_device.device_code if c.used_by_device else "",
            ]
        )

    filename = f"viorafilm_coupons_{timezone.localtime(timezone.now(), tzinfo).strftime('%Y%m%d_%H%M%S')}.csv"
    return _csv_response(
        filename=filename,
        headers=[
            "formatted_code",
            "code",
            "currency",
            "amount",
            "status",
            "created_at",
            "expires_at",
            "used_at",
            "org_code",
            "branch_code",
            "used_session_id",
            "used_device_code",
        ],
        rows=rows,
    )


@login_required(login_url="/dashboard/login")
@never_cache
def photos_view(request):
    filters = _resolve_scope_filters(request.user, request)
    context, tzinfo = _build_dashboard_page_context(request.user, filters)
    q = (request.GET.get("q") or "").strip()
    devices_qs = _apply_org_branch_filter(_scoped_devices(request.user), "org_id", "branch_id", filters)
    device_ids = list(devices_qs.values_list("id", flat=True))
    now = timezone.now()
    sessions_qs = ShareSession.objects.select_related("device").filter(device_id__in=device_ids)
    if q:
        sessions_qs = sessions_qs.filter(token__icontains=q)
    else:
        sessions_qs = sessions_qs.filter(created_at__gte=now - timedelta(days=7))
    sessions = sessions_qs.order_by("-created_at")[:300]

    rows = []
    for s in sessions:
        assets = s.assets if isinstance(s.assets, dict) else {}
        files = s.files if isinstance(s.files, dict) else {}

        print_url = generate_download_url_from_meta(files.get("print"), request=request)
        frame_url = generate_download_url_from_meta(files.get("frame"), request=request)
        gif_url = generate_download_url_from_meta(files.get("gif"), request=request)
        video_url = generate_download_url_from_meta(files.get("video"), request=request)
        original_urls = []
        for meta in files.get("original") or []:
            u = generate_download_url_from_meta(meta, request=request)
            if u:
                original_urls.append(u)

        # Backward compatibility for old rows that only have assets URLs.
        print_url = print_url or assets.get("print_url", "")
        frame_url = frame_url or assets.get("frame_url", "")
        gif_url = gif_url or assets.get("gif_url", "")
        video_url = video_url or assets.get("video_url", "")
        if not original_urls:
            raw_originals = assets.get("original_urls")
            if isinstance(raw_originals, list):
                original_urls = raw_originals

        if not isinstance(original_urls, list):
            original_urls = []
        is_expired = s.is_expired()
        rows.append(
            {
                "session": s,
                "share_url": request.build_absolute_uri(f"/s/{s.token}/"),
                "assets_summary": ", ".join(sorted(files.keys())) if files else (", ".join(sorted(assets.keys())) if assets else "-"),
                "assets": assets,
                "is_expired": is_expired,
                "print_url": print_url,
                "gif_url": gif_url,
                "video_url": video_url,
                "frame_url": frame_url,
                "original_urls": original_urls,
            }
        )
    context.update(
        {
            "rows": rows,
            "q": q,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        }
    )
    return _render_dashboard_page(request, "dashboard/photos.html", context, tzinfo)
