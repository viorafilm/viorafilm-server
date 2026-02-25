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


def _resolve_alert(device: Device, alert_type: str):
    alert = Alert.objects.filter(device=device, alert_type=alert_type, resolved_at__isnull=True).first()
    if alert:
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["resolved_at"])


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
            notify(device, "Kiosk OFFLINE", f"{device.device_code} is offline.\nlast_seen_at={device.last_seen_at}")
            alert.last_notified_at = timezone.now()
            alert.save(update_fields=["last_notified_at"])

    for device in online:
        _resolve_alert(device, AlertType.OFFLINE)


@shared_task
def check_device_health():
    devices = Device.objects.filter(is_active=True)
    for device in devices:
        health = device.last_health_json or {}
        internet_ok = health.get("internet_ok", True)
        camera_ok = health.get("camera_ok", True)

        printer_ok = health.get("printer_ok", True)
        ds620 = health.get("printer_ds620") or {}
        rx1hs = health.get("printer_rx1hs") or {}
        if isinstance(ds620, dict) and "ok" in ds620:
            printer_ok = printer_ok and bool(ds620.get("ok"))
        if isinstance(rx1hs, dict) and "ok" in rx1hs:
            printer_ok = printer_ok and bool(rx1hs.get("ok"))

        if not internet_ok:
            alert = _open_alert(device, AlertType.INTERNET_OFFLINE, Severity.WARN, "Internet disconnected")
            if _should_notify(alert):
                notify(device, "Internet OFFLINE", f"{device.device_code}: internet disconnected")
                alert.last_notified_at = timezone.now()
                alert.save(update_fields=["last_notified_at"])
        else:
            _resolve_alert(device, AlertType.INTERNET_OFFLINE)

        if not camera_ok:
            alert = _open_alert(device, AlertType.CAMERA_OFFLINE, Severity.WARN, "Camera disconnected")
            if _should_notify(alert):
                notify(device, "Camera OFFLINE", f"{device.device_code}: camera disconnected")
                alert.last_notified_at = timezone.now()
                alert.save(update_fields=["last_notified_at"])
        else:
            _resolve_alert(device, AlertType.CAMERA_OFFLINE)

        if not printer_ok:
            alert = _open_alert(device, AlertType.PRINTER_OFFLINE, Severity.WARN, "Printer offline / paper low")
            if _should_notify(alert):
                notify(device, "Printer OFFLINE", f"{device.device_code}: printer offline/paper low")
                alert.last_notified_at = timezone.now()
                alert.save(update_fields=["last_notified_at"])
        else:
            _resolve_alert(device, AlertType.PRINTER_OFFLINE)

