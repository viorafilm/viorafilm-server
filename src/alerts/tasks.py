import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.models import Device
from sales.models import SaleTransaction

from .models import Alert, AlertType, ChannelType, NotificationChannel, Severity
from .notifier import notify, parse_email_targets, send_email_targets

logger = logging.getLogger(__name__)


def _should_notify(alert: Alert) -> bool:
    cooldown = getattr(settings, "ALERT_NOTIFY_COOLDOWN_SECONDS", 600)
    if not alert.last_notified_at:
        return True
    return (timezone.now() - alert.last_notified_at) >= timedelta(seconds=cooldown)


def _open_alert(device: Device, alert_type: str, severity: str, message: str) -> Alert:
    alert = Alert.objects.filter(device=device, alert_type=alert_type, resolved_at__isnull=True).first()
    if alert:
        if alert.message != message:
            alert.message = message
            alert.save(update_fields=["message"])
        return alert
    return Alert.objects.create(device=device, alert_type=alert_type, severity=severity, message=message)


def _resolve_alert(device: Device, alert_type: str) -> bool:
    alert = Alert.objects.filter(device=device, alert_type=alert_type, resolved_at__isnull=True).first()
    if not alert:
        return False
    alert.resolved_at = timezone.now()
    alert.save(update_fields=["resolved_at"])
    return True


def _device_context(device: Device):
    org = getattr(device, "org", None)
    branch = getattr(device, "branch", None)
    return {
        "device_code": device.device_code,
        "display_name": device.display_name or "-",
        "org_code": getattr(org, "code", "-"),
        "branch_code": getattr(branch, "code", "-"),
        "last_seen_at": device.last_seen_at,
    }


def _build_subject(alert_type: str, severity: str, ko: str, en: str) -> str:
    return f"[Viorafilm][{severity}][{alert_type}] {ko} / {en}"


def _build_body(device: Device, headline_ko: str, headline_en: str, detail_ko: str = "", detail_en: str = "") -> str:
    ctx = _device_context(device)
    now_local = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
    last_seen = ctx["last_seen_at"] or "-"
    lines = [
        f"[KO] {headline_ko}",
        f"시간: {now_local}",
        f"조직/지점: {ctx['org_code']} / {ctx['branch_code']}",
        f"장치코드: {ctx['device_code']}",
        f"표시이름: {ctx['display_name']}",
        f"마지막 통신: {last_seen}",
    ]
    if detail_ko:
        lines.append(f"상세: {detail_ko}")
    lines += [
        "",
        f"[EN] {headline_en}",
        f"Time: {now_local}",
        f"Org/Branch: {ctx['org_code']} / {ctx['branch_code']}",
        f"Device Code: {ctx['device_code']}",
        f"Display Name: {ctx['display_name']}",
        f"Last Seen: {last_seen}",
    ]
    if detail_en:
        lines.append(f"Detail: {detail_en}")
    return "\n".join(str(x) for x in lines)


def _notify_alert(device: Device, alert: Alert, ko: str, en: str, detail_ko: str = "", detail_en: str = ""):
    title = _build_subject(alert.alert_type, alert.severity, ko, en)
    body = _build_body(device, ko, en, detail_ko=detail_ko, detail_en=detail_en)
    notify(device, title, body)
    alert.last_notified_at = timezone.now()
    alert.save(update_fields=["last_notified_at"])


def _notify_recovery(device: Device, alert_type: str, ko: str, en: str):
    if not bool(getattr(settings, "ALERT_NOTIFY_RECOVERY", True)):
        return
    title = f"[Viorafilm][RECOVERY][{alert_type}] {ko} / {en}"
    body = _build_body(device, ko, en)
    notify(device, title, body)


def _printer_state(health: dict):
    printer_ok = health.get("printer_ok", True)
    ds620 = health.get("printer_ds620") or {}
    rx1hs = health.get("printer_rx1hs") or {}
    if isinstance(ds620, dict) and "ok" in ds620:
        printer_ok = printer_ok and bool(ds620.get("ok"))
    if isinstance(rx1hs, dict) and "ok" in rx1hs:
        printer_ok = printer_ok and bool(rx1hs.get("ok"))
    detail_ko = f"DS620={ds620 or '-'}, RX1HS={rx1hs or '-'}"
    detail_en = f"DS620={ds620 or '-'}, RX1HS={rx1hs or '-'}"
    return printer_ok, detail_ko, detail_en


def _channel_targets(channel: NotificationChannel):
    targets = parse_email_targets(channel.config.get("to"))
    if not targets:
        targets = parse_email_targets(channel.config.get("recipients"))
    return targets


def _count_locked_devices(devices):
    return sum(
        1
        for device in devices
        if bool(getattr(device, "is_locked", False))
        or (isinstance(device.last_health_json, dict) and bool(device.last_health_json.get("offline_lock_active")))
    )


def _format_money(amount: int) -> str:
    return f"{int(amount):,}"


def _build_daily_report_body(
    scope_name: str,
    date_str: str,
    tx_count: int,
    total_amount: int,
    cash_amount: int,
    coupon_amount: int,
    online_count: int,
    offline_count: int,
    locked_count: int,
    open_alert_count: int,
    open_by_type: dict,
    top_branches: list,
):
    open_lines = ", ".join(f"{k}:{v}" for k, v in sorted(open_by_type.items())) if open_by_type else "-"
    top_branch_ko = []
    top_branch_en = []
    top_n_label = max(1, len(top_branches))
    for idx, row in enumerate(top_branches, start=1):
        code = row.get("branch__code") or "-"
        total = int(row.get("total_amount") or 0)
        tx = int(row.get("tx_count") or 0)
        top_branch_ko.append(f"{idx}. {code}: KRW {_format_money(total)} ({tx}\uAC74)")
        top_branch_en.append(f"{idx}. {code}: KRW {_format_money(total)} ({tx} tx)")
    if not top_branch_ko:
        top_branch_ko = ["-"]
    if not top_branch_en:
        top_branch_en = ["-"]
    lines = [
        f"[KO] 비오라필름 일일 운영 리포트 ({scope_name})",
        f"날짜: {date_str}",
        f"거래 건수: {tx_count}",
        f"총 매출: KRW {_format_money(total_amount)}",
        f"현금 합계: KRW {_format_money(cash_amount)}",
        f"쿠폰 합계: KRW {_format_money(coupon_amount)}",
        f"장치 온라인/오프라인: {online_count}/{offline_count}",
        f"잠금 장치 수: {locked_count}",
        f"미해결 알림 수: {open_alert_count}",
        f"미해결 알림 타입: {open_lines}",
        f"지점별 매출 TOP {top_n_label}:",
        *top_branch_ko,
        "",
        f"[EN] Viorafilm Daily Operations Report ({scope_name})",
        f"Date: {date_str}",
        f"Transactions: {tx_count}",
        f"Total Sales: KRW {_format_money(total_amount)}",
        f"Cash Total: KRW {_format_money(cash_amount)}",
        f"Coupon Total: KRW {_format_money(coupon_amount)}",
        f"Devices Online/Offline: {online_count}/{offline_count}",
        f"Locked Devices: {locked_count}",
        f"Open Alerts: {open_alert_count}",
        f"Open Alert Types: {open_lines}",
        f"Top Branches by Sales (Top {top_n_label}):",
        *top_branch_en,
    ]
    return "\n".join(lines)


@shared_task
def check_device_offline():
    threshold = getattr(settings, "OFFLINE_THRESHOLD_SECONDS", 120)
    cutoff = timezone.now() - timedelta(seconds=threshold)

    offline = Device.objects.filter(is_active=True).filter(Q(last_seen_at__lt=cutoff) | Q(last_seen_at__isnull=True))
    online = Device.objects.filter(is_active=True, last_seen_at__gte=cutoff)

    for device in offline:
        alert = _open_alert(
            device,
            AlertType.OFFLINE,
            Severity.CRITICAL,
            f"Device offline (last_seen_at={device.last_seen_at})",
        )
        if _should_notify(alert):
            _notify_alert(
                device,
                alert,
                ko="장치 오프라인 상태입니다.",
                en="Device is offline.",
                detail_ko=f"마지막 통신 시각: {device.last_seen_at}",
                detail_en=f"Last seen at: {device.last_seen_at}",
            )

    for device in online:
        if _resolve_alert(device, AlertType.OFFLINE):
            _notify_recovery(device, AlertType.OFFLINE, "장치 오프라인이 복구되었습니다.", "Device offline recovered.")


@shared_task
def check_device_health():
    devices = Device.objects.filter(is_active=True)
    for device in devices:
        health = device.last_health_json if isinstance(device.last_health_json, dict) else {}
        internet_ok = health.get("internet_ok", True)
        camera_ok = health.get("camera_ok", True)
        printer_ok, printer_detail_ko, printer_detail_en = _printer_state(health)

        if not internet_ok:
            alert = _open_alert(device, AlertType.INTERNET_OFFLINE, Severity.WARN, "Internet disconnected")
            if _should_notify(alert):
                _notify_alert(
                    device,
                    alert,
                    ko="인터넷 연결이 끊겼습니다.",
                    en="Internet connection is down.",
                )
        else:
            if _resolve_alert(device, AlertType.INTERNET_OFFLINE):
                _notify_recovery(
                    device,
                    AlertType.INTERNET_OFFLINE,
                    "인터넷 연결이 복구되었습니다.",
                    "Internet connection recovered.",
                )

        if not camera_ok:
            alert = _open_alert(device, AlertType.CAMERA_OFFLINE, Severity.WARN, "Camera disconnected")
            if _should_notify(alert):
                _notify_alert(
                    device,
                    alert,
                    ko="카메라 연결이 끊겼습니다.",
                    en="Camera connection is down.",
                )
        else:
            if _resolve_alert(device, AlertType.CAMERA_OFFLINE):
                _notify_recovery(
                    device,
                    AlertType.CAMERA_OFFLINE,
                    "카메라 연결이 복구되었습니다.",
                    "Camera connection recovered.",
                )

        if not printer_ok:
            alert = _open_alert(device, AlertType.PRINTER_OFFLINE, Severity.WARN, "Printer offline / paper low")
            if _should_notify(alert):
                _notify_alert(
                    device,
                    alert,
                    ko="프린터 상태를 확인하세요. (오프라인/용지/오류 가능)",
                    en="Check printer status (offline/paper/error).",
                    detail_ko=printer_detail_ko,
                    detail_en=printer_detail_en,
                )
        else:
            if _resolve_alert(device, AlertType.PRINTER_OFFLINE):
                _notify_recovery(
                    device,
                    AlertType.PRINTER_OFFLINE,
                    "프린터 상태가 복구되었습니다.",
                    "Printer status recovered.",
                )


@shared_task
def send_daily_ops_report():
    if not bool(getattr(settings, "ALERT_DAILY_REPORT_ENABLED", True)):
        return

    threshold = int(getattr(settings, "OFFLINE_THRESHOLD_SECONDS", 120))
    cutoff = timezone.now() - timedelta(seconds=threshold)
    now_local = timezone.localtime()
    day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    today = day_start.date()
    top_n = int(getattr(settings, "ALERT_DAILY_TOP_BRANCHES", 5))

    channels = NotificationChannel.objects.filter(enabled=True, type=ChannelType.EMAIL).select_related("org")
    for channel in channels:
        targets = _channel_targets(channel)
        if not targets:
            continue

        org = channel.org
        scope_name = f"ORG:{org.code}" if org else "GLOBAL"

        sales_qs = SaleTransaction.objects.filter(created_at__gte=day_start, created_at__lt=day_end)
        devices_qs = Device.objects.filter(is_active=True)
        alerts_qs = Alert.objects.filter(resolved_at__isnull=True)
        if org:
            sales_qs = sales_qs.filter(org=org)
            devices_qs = devices_qs.filter(org=org)
            alerts_qs = alerts_qs.filter(device__org=org)

        sales_agg = sales_qs.aggregate(
            tx_count=Count("id"),
            total_amount=Sum("price_total"),
            cash_amount=Sum("amount_cash"),
            coupon_amount=Sum("amount_coupon"),
        )
        tx_count = int(sales_agg.get("tx_count") or 0)
        total_amount = int(sales_agg.get("total_amount") or 0)
        cash_amount = int(sales_agg.get("cash_amount") or 0)
        coupon_amount = int(sales_agg.get("coupon_amount") or 0)

        online_count = devices_qs.filter(last_seen_at__gte=cutoff).count()
        offline_count = devices_qs.filter(Q(last_seen_at__lt=cutoff) | Q(last_seen_at__isnull=True)).count()
        devices = list(devices_qs.only("last_health_json"))
        locked_count = _count_locked_devices(devices)
        open_alert_count = alerts_qs.count()
        open_by_type = {row["alert_type"]: row["c"] for row in alerts_qs.values("alert_type").annotate(c=Count("id"))}
        top_branches = list(
            sales_qs.values("branch__code")
            .annotate(total_amount=Sum("price_total"), tx_count=Count("id"))
            .order_by("-total_amount", "branch__code")[: max(1, top_n)]
        )

        subject = f"[Viorafilm][Daily Report] {today.isoformat()} ({scope_name})"
        body = _build_daily_report_body(
            scope_name=scope_name,
            date_str=today.isoformat(),
            tx_count=tx_count,
            total_amount=total_amount,
            cash_amount=cash_amount,
            coupon_amount=coupon_amount,
            online_count=online_count,
            offline_count=offline_count,
            locked_count=locked_count,
            open_alert_count=open_alert_count,
            open_by_type=open_by_type,
            top_branches=top_branches,
        )
        sent, failed = send_email_targets(targets, subject, body)
        logger.info(
            "[ALERT][DAILY_REPORT] scope=%s sent=%s failed=%s targets=%s tx=%s total=%s",
            scope_name,
            sent,
            failed,
            ",".join(targets),
            tx_count,
            total_amount,
        )
