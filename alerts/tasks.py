from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from core.models import Device

from .models import Alert
from .service import open_or_update_alert, resolve_alert


def _as_optional_bool(value):
    if isinstance(value, bool):
        return value
    return None


def _derive_printer_ok(payload: dict) -> bool | None:
    direct = _as_optional_bool(payload.get("printer_ok"))
    if direct is not None:
        return direct

    values: list[bool] = []
    for key in ("printer_ds620", "printer_rx1hs"):
        item = payload.get(key)
        if isinstance(item, dict):
            val = _as_optional_bool(item.get("ok"))
            if val is not None:
                values.append(val)
    if not values:
        return None
    return any(values)


@shared_task(name="alerts.tasks.check_device_offline")
def check_device_offline():
    try:
        threshold_sec = max(1, int(getattr(settings, "ALERT_OFFLINE_SECONDS", 120)))
    except (TypeError, ValueError):
        threshold_sec = 120
    cutoff = timezone.now() - timedelta(seconds=threshold_sec)

    for device in Device.objects.filter(is_active=True).select_related("org", "branch"):
        if device.last_seen_at is None or device.last_seen_at < cutoff:
            last_seen = device.last_seen_at.isoformat() if device.last_seen_at else "never"
            message = f"No heartbeat for >= {threshold_sec}s (last_seen_at={last_seen})"
            open_or_update_alert(
                device=device,
                alert_type=Alert.TYPE_OFFLINE,
                severity=Alert.SEVERITY_CRITICAL,
                message=message,
            )
        else:
            resolve_alert(device, Alert.TYPE_OFFLINE)


@shared_task(name="alerts.tasks.check_device_health")
def check_device_health():
    for device in Device.objects.filter(is_active=True).select_related("org", "branch"):
        payload = device.last_health_json if isinstance(device.last_health_json, dict) else {}

        printer_ok = _derive_printer_ok(payload)
        camera_ok = _as_optional_bool(payload.get("camera_ok"))
        internet_ok = _as_optional_bool(payload.get("internet_ok"))

        if printer_ok is False:
            open_or_update_alert(
                device=device,
                alert_type=Alert.TYPE_PRINTER_OFFLINE,
                severity=Alert.SEVERITY_WARN,
                message="Printer health reported offline/error.",
            )
        elif printer_ok is True:
            resolve_alert(device, Alert.TYPE_PRINTER_OFFLINE)

        if camera_ok is False:
            open_or_update_alert(
                device=device,
                alert_type=Alert.TYPE_CAMERA_OFFLINE,
                severity=Alert.SEVERITY_WARN,
                message="Camera health reported offline/error.",
            )
        elif camera_ok is True:
            resolve_alert(device, Alert.TYPE_CAMERA_OFFLINE)

        if internet_ok is False:
            open_or_update_alert(
                device=device,
                alert_type=Alert.TYPE_INTERNET_OFFLINE,
                severity=Alert.SEVERITY_WARN,
                message="Internet health reported offline/error.",
            )
        elif internet_ok is True:
            resolve_alert(device, Alert.TYPE_INTERNET_OFFLINE)
