from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from core.models import Device

from .models import Alert, NotificationChannel
from .notifier import send_email, send_slack


def _cooldown_seconds() -> int:
    try:
        return max(0, int(getattr(settings, "ALERT_NOTIFY_COOLDOWN_SECONDS", 600)))
    except (TypeError, ValueError):
        return 600


def _channel_queryset_for_device(device: Device):
    return NotificationChannel.objects.filter(enabled=True).filter(
        Q(org__isnull=True) | Q(org=device.org)
    )


def _message_title(alert: Alert) -> str:
    return f"[ALERT] {alert.alert_type} {alert.device.device_code}"


def _message_body(alert: Alert) -> str:
    return (
        f"Device: {alert.device.device_code}\n"
        f"Alert: {alert.alert_type}\n"
        f"Severity: {alert.severity}\n"
        f"Message: {alert.message}\n"
        f"CreatedAt: {alert.created_at.isoformat()}\n"
    )


def notify_alert(alert: Alert, force: bool = False) -> bool:
    now = timezone.now()
    cooldown = timedelta(seconds=_cooldown_seconds())
    if not force and alert.last_notified_at and now - alert.last_notified_at < cooldown:
        return False

    text = _message_body(alert)
    subject = _message_title(alert)
    sent_any = False
    for channel in _channel_queryset_for_device(alert.device):
        cfg = channel.config if isinstance(channel.config, dict) else {}
        if channel.type == NotificationChannel.TYPE_SLACK:
            webhook = str(cfg.get("webhook_url") or cfg.get("webhook") or "").strip()
            sent_any = send_slack(webhook, text) or sent_any
        elif channel.type == NotificationChannel.TYPE_EMAIL:
            recipients = cfg.get("to") or cfg.get("recipients") or cfg.get("recipient")
            sent_any = send_email(recipients, subject, text) or sent_any
        elif channel.type == NotificationChannel.TYPE_KAKAO:
            # Placeholder for future Kakao integration.
            continue

    if sent_any:
        alert.last_notified_at = now
        alert.save(update_fields=["last_notified_at"])
    return sent_any


def open_or_update_alert(
    device: Device,
    alert_type: str,
    severity: str,
    message: str,
) -> Alert:
    alert = (
        Alert.objects.filter(
            device=device,
            alert_type=alert_type,
            resolved_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if alert is None:
        alert = Alert.objects.create(
            device=device,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
    else:
        changed = False
        if alert.message != message:
            alert.message = message
            changed = True
        if alert.severity != severity:
            alert.severity = severity
            changed = True
        if changed:
            alert.save(update_fields=["message", "severity"])
    notify_alert(alert, force=False)
    return alert


def resolve_alert(device: Device, alert_type: str) -> bool:
    alert = (
        Alert.objects.filter(
            device=device,
            alert_type=alert_type,
            resolved_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if alert is None:
        return False
    alert.resolved_at = timezone.now()
    alert.save(update_fields=["resolved_at"])
    return True

