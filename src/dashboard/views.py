from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import UserRole
from alerts.models import ChannelType, NotificationChannel
from audit.service import log_event
from core.models import Branch, Device, Organization
from coupons.models import Coupon
from coupons.service import create_batch_and_coupons
from mediahub.models import ShareSession
from sales.models import SaleTransaction
from storagehub.service import generate_download_url_from_meta


def _is_super(user):
    return getattr(user, "role", None) == UserRole.SUPERADMIN


def _is_org_admin(user):
    return getattr(user, "role", None) == UserRole.ORG_ADMIN


def _is_branch_admin(user):
    return getattr(user, "role", None) == UserRole.BRANCH_ADMIN


def _is_viewer(user):
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


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "dashboard_index")
    return render(request, "dashboard/login.html", {"form": form})


@login_required(login_url="/dashboard/login")
def index_view(request):
    sales = _scoped_sales(request.user)
    today = timezone.localdate()
    now = timezone.localtime()
    today_total = sales.filter(created_at__date=today).aggregate(v=Sum("price_total"))["v"] or 0
    month_total = sales.filter(created_at__year=now.year, created_at__month=now.month).aggregate(v=Sum("price_total"))["v"] or 0
    return render(
        request,
        "dashboard/index.html",
        {
            "today_total": today_total,
            "month_total": month_total,
            "sales_count": sales.count(),
            "can_edit": not _is_viewer(request.user),
        },
    )


@login_required(login_url="/dashboard/login")
def devices_view(request):
    user = request.user
    can_edit_notifications = not _is_viewer(user)
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
        return redirect("dashboard_devices")

    devices = _scoped_devices(user)
    now = timezone.now()
    threshold = int(getattr(settings, "OFFLINE_THRESHOLD_SECONDS", 120))
    rows = []
    for d in devices[:300]:
        health = d.last_health_json if isinstance(d.last_health_json, dict) else {}
        online = bool(d.last_seen_at and (now - d.last_seen_at).total_seconds() < threshold)
        rows.append(
            {
                "device": d,
                "online": online,
                "internet_ok": health.get("internet_ok"),
                "camera_ok": health.get("camera_ok"),
                "printer_ok": _derive_printer_ok(health),
                "offline_guard_enabled": bool(health.get("offline_guard_enabled", False)),
                "offline_lock_active": bool(health.get("offline_lock_active", False)),
                "offline_grace_remaining_seconds": _as_optional_int(
                    health.get("offline_grace_remaining_seconds")
                ),
                "offline_last_online_at": health.get("offline_last_online_at"),
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
    if only_locked:
        rows = [row for row in rows if row.get("offline_lock_active")]

    return render(
        request,
        "dashboard/devices.html",
        {
            "rows": rows,
            "only_locked": only_locked,
            "can_edit_notifications": can_edit_notifications,
            "alert_emails_text": ", ".join(_get_scope_email_targets(user)),
        },
    )


@login_required(login_url="/dashboard/login")
def sales_view(request):
    sales = _scoped_sales(request.user)[:200]
    return render(request, "dashboard/sales.html", {"sales": sales})


@login_required(login_url="/dashboard/login")
def coupons_view(request):
    user = request.user
    can_edit = not _is_viewer(user)
    coupons = _scoped_coupons(user)

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Viewer is read-only")
        action = (request.POST.get("action") or "").strip()

        if action == "issue":
            amount = int(request.POST.get("amount") or 0)
            count = int(request.POST.get("count") or 0)
            title = (request.POST.get("title") or "").strip()
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

            if amount <= 0 or count <= 0:
                messages.error(request, "amount/count must be > 0")
            else:
                batch = create_batch_and_coupons(
                    org=org,
                    branch=branch,
                    amount=amount,
                    count=count,
                    created_by=user,
                    title=title,
                )
                messages.success(request, f"Coupon batch issued: #{batch.id}")

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

        return redirect("dashboard_coupons")

    return render(
        request,
        "dashboard/coupons.html",
        {
            "coupons": coupons[:500],
            "orgs": _available_orgs(user),
            "branches": _available_branches(user),
            "can_edit": can_edit,
        },
    )


@login_required(login_url="/dashboard/login")
def photos_view(request):
    q = (request.GET.get("q") or "").strip()
    now = timezone.now()
    device_ids = list(_scoped_devices(request.user).values_list("id", flat=True))
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
    return render(request, "dashboard/photos.html", {"rows": rows, "q": q})

