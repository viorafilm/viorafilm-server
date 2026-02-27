from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from core.models import Device

from .models import Alert, AlertType, Severity
from .notifier import notify


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
