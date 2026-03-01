import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import UserRole
from alerts.notifier import send_email_targets
from alerts.models import ChannelType, NotificationChannel
from audit.service import log_event
from core.models import Branch, Device, Organization
from coupons.models import Coupon
from coupons.service import (
    MAX_COUPON_BATCH_COUNT,
    MAX_TOTAL_COUPONS,
    create_batch_and_coupons,
    resolve_expires_hours,
)
from mediahub.models import ShareSession
from sales.models import SaleTransaction
from storagehub.service import generate_download_url_from_meta
from urllib.parse import urlencode

AI_EST_USD_PER_IMAGE = 0.039
AI_EST_KRW_PER_USD = 1400.0
AI_EST_DEFAULT_IMAGES_PER_SALE = 2
AI_EST_SERVER_COST_MULTIPLIER = 10.0
AI_EST_KRW_PER_IMAGE = int(round(AI_EST_USD_PER_IMAGE * AI_EST_KRW_PER_USD))


def _is_super(user):
    return getattr(user, "role", None) == UserRole.SUPERADMIN


def _is_org_admin(user):
    return getattr(user, "role", None) == UserRole.ORG_ADMIN


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


def _build_sales_summary(user):
    sales = _scoped_sales(user)
    today = timezone.localdate()
    now_local = timezone.localtime()
    today_total = sales.filter(created_at__date=today).aggregate(v=Sum("price_total"))["v"] or 0
    month_total = (
        sales.filter(created_at__year=now_local.year, created_at__month=now_local.month).aggregate(v=Sum("price_total"))["v"]
        or 0
    )
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


def _resolve_sales_period(request):
    period = str(request.GET.get("period") or "month").strip().lower()
    if period not in {"week", "month", "custom"}:
        period = "month"

    today = timezone.localdate()
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


def _apply_sales_period_filter(qs, period_info):
    start_date = period_info.get("start_date")
    end_date = period_info.get("end_date")
    if start_date is not None:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date is not None:
        qs = qs.filter(created_at__date__lte=end_date)
    return qs


def _build_sales_chart_payload(sales_qs):
    rows = list(
        sales_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("price_total"), tx_count=Count("id"))
        .order_by("day")
    )
    return {
        "labels": [str(row["day"]) for row in rows],
        "totals": [int(row.get("total") or 0) for row in rows],
        "counts": [int(row.get("tx_count") or 0) for row in rows],
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


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "dashboard_index")
    return render(request, "dashboard/login.html", {"form": form})


@login_required(login_url="/dashboard/login")
@never_cache
def index_view(request):
    summary = _build_sales_summary(request.user)
    return render(
        request,
        "dashboard/index.html",
        {
            "today_total": summary["today_total"],
            "month_total": summary["month_total"],
            "sales_count": summary["sales_count"],
            "can_edit": not _is_viewer(request.user),
        },
    )


@login_required(login_url="/dashboard/login")
@never_cache
def index_live_view(request):
    summary = _build_sales_summary(request.user)
    summary["ok"] = True
    summary["generated_at"] = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse(summary)


@login_required(login_url="/dashboard/login")
@never_cache
def devices_view(request):
    user = request.user
    filters = _resolve_scope_filters(user, request)
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
            now_local = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
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

    return render(
        request,
        "dashboard/devices.html",
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
        },
    )


@login_required(login_url="/dashboard/login")
@never_cache
def devices_live_view(request):
    user = request.user
    filters = _resolve_scope_filters(user, request)
    only_locked = str(request.GET.get("locked", "")).strip() == "1"
    filtered_devices = _apply_org_branch_filter(_scoped_devices(user), "org_id", "branch_id", filters)
    rows = _build_device_rows(user, only_locked=only_locked, devices_qs=filtered_devices)
    can_manage_locks = not _is_viewer(user)
    tbody_html = render_to_string(
        "dashboard/_devices_tbody.html",
        {
            "rows": rows,
            "can_manage_locks": can_manage_locks,
        },
        request=request,
    )
    return JsonResponse(
        {
            "ok": True,
            "generated_at": timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(rows),
            "tbody_html": tbody_html,
        }
    )


@login_required(login_url="/dashboard/login")
@never_cache
def sales_view(request):
    filters = _resolve_scope_filters(request.user, request)
    period_info = _resolve_sales_period(request)
    sales_base_qs = _apply_org_branch_filter(_scoped_sales(request.user), "org_id", "branch_id", filters)
    sales_qs = _apply_sales_period_filter(sales_base_qs, period_info)
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

    ai_estimated_server_cost = int(ai_generated_images * AI_EST_KRW_PER_IMAGE)
    ai_estimated_billing_server_cost = int(round(ai_estimated_server_cost * AI_EST_SERVER_COST_MULTIPLIER))

    chart_payload = _build_sales_chart_payload(sales_qs)
    return render(
        request,
        "dashboard/sales.html",
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
            "ai_estimated_billing_server_cost": ai_estimated_billing_server_cost,
            "ai_est_krw_per_image": AI_EST_KRW_PER_IMAGE,
            "ai_est_server_cost_multiplier": AI_EST_SERVER_COST_MULTIPLIER,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        },
    )


@login_required(login_url="/dashboard/login")
@never_cache
def sales_export_view(request):
    filters = _resolve_scope_filters(request.user, request)
    period_info = _resolve_sales_period(request)
    sales_qs = _apply_org_branch_filter(_scoped_sales(request.user), "org_id", "branch_id", filters)
    sales_qs = _apply_sales_period_filter(sales_qs, period_info)

    rows = []
    for s in sales_qs.order_by("-created_at").iterator():
        meta = s.meta if isinstance(s.meta, dict) else {}
        compose_mode = str(meta.get("compose_mode", "normal")).strip().lower() or "normal"
        if compose_mode not in {"normal", "ai", "celebrity"}:
            compose_mode = "normal"
        rows.append(
            [
                timezone.localtime(s.created_at).strftime("%Y-%m-%d %H:%M:%S"),
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

    filename = f"viorafilm_sales_{timezone.localtime().strftime('%Y%m%d_%H%M%S')}.csv"
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
    can_edit = not _is_viewer(user)
    coupons = _apply_org_branch_filter(
        _scoped_coupons(user),
        "batch__org_id",
        "batch__branch_id",
        filters,
    )
    coupon_total_count = int(Coupon.objects.count())
    coupon_remaining_capacity = max(0, int(MAX_TOTAL_COUPONS - coupon_total_count))

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
                    messages.success(request, f"Coupon batch issued: #{batch.id}")
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

        params = _query_params_from_filters(filters)
        if params:
            return redirect(f"/dashboard/coupons?{urlencode(params)}")
        return redirect("dashboard_coupons")

    return render(
        request,
        "dashboard/coupons.html",
        {
            "coupons": coupons[:500],
            "orgs": _available_orgs(user),
            "branches": _available_branches(user),
            "can_edit": can_edit,
            "coupon_total_count": coupon_total_count,
            "coupon_remaining_capacity": coupon_remaining_capacity,
            "coupon_max_total": int(MAX_TOTAL_COUPONS),
            "coupon_max_per_issue": int(MAX_COUPON_BATCH_COUNT),
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        },
    )


@login_required(login_url="/dashboard/login")
@never_cache
def coupons_export_view(request):
    filters = _resolve_scope_filters(request.user, request)
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
                timezone.localtime(c.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                timezone.localtime(c.expires_at).strftime("%Y-%m-%d %H:%M:%S"),
                timezone.localtime(c.used_at).strftime("%Y-%m-%d %H:%M:%S") if c.used_at else "",
                getattr(c.batch.org, "code", "") if c.batch else "",
                getattr(c.batch.branch, "code", "") if c.batch else "",
                c.used_session_id or "",
                c.used_by_device.device_code if c.used_by_device else "",
            ]
        )

    filename = f"viorafilm_coupons_{timezone.localtime().strftime('%Y%m%d_%H%M%S')}.csv"
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
    q = (request.GET.get("q") or "").strip()
    now = timezone.now()
    devices_qs = _apply_org_branch_filter(_scoped_devices(request.user), "org_id", "branch_id", filters)
    device_ids = list(devices_qs.values_list("id", flat=True))
    sessions_qs = ShareSession.objects.select_related("device").filter(
        device_id__in=device_ids,
        expires_at__gt=now,
    )
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
    return render(
        request,
        "dashboard/photos.html",
        {
            "rows": rows,
            "q": q,
            "filter_org_id": filters["org_id"],
            "filter_branch_id": filters["branch_id"],
            "filter_orgs": filters["orgs"],
            "filter_branches": filters["branches"],
        },
    )
