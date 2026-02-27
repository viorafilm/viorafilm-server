import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

from core.models import Device

from .models import ChannelType, NotificationChannel

logger = logging.getLogger(__name__)


def _channels_for_device(device: Device):
    queryset = NotificationChannel.objects.filter(enabled=True).filter(Q(org=device.org) | Q(org__isnull=True))
    return list(queryset)


def parse_email_targets(raw_value):
    if isinstance(raw_value, list):
        values = [str(v).strip() for v in raw_value if str(v).strip()]
    elif isinstance(raw_value, str):
        text = raw_value.replace(";", ",")
        values = [x.strip() for x in text.split(",") if x.strip()]
    else:
        values = []
    seen = set()
    deduped = []
    for email in values:
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(email)
    return deduped


def send_email_targets(targets, title: str, text: str):
    sent = 0
    failed = 0
    for target in targets:
        try:
            send_mail(
                title,
                text,
                settings.DEFAULT_FROM_EMAIL,
                [target],
                fail_silently=False,
            )
            sent += 1
        except Exception:
            failed += 1
            logger.exception("[ALERT][EMAIL] send failed target=%s title=%s", target, title)
    return sent, failed


def notify(device: Device, title: str, text: str):
    channels = _channels_for_device(device)
    for channel in channels:
        if channel.type == ChannelType.SLACK:
            if not bool(getattr(settings, "ALERT_USE_SLACK", False)):
                continue
            webhook = channel.config.get("webhook_url")
            if webhook:
                try:
                    requests.post(webhook, json={"text": f"{title}\n{text}"}, timeout=5)
                except Exception:
                    logger.exception("[ALERT][SLACK] send failed device=%s", device.device_code)
        elif channel.type == ChannelType.EMAIL:
            targets = parse_email_targets(channel.config.get("to"))
            if not targets:
                targets = parse_email_targets(channel.config.get("recipients"))
            if not targets:
                continue
            sent, failed = send_email_targets(targets, title, text)
            logger.info(
                "[ALERT][EMAIL] device=%s sent=%s failed=%s targets=%s",
                device.device_code,
                sent,
                failed,
                ",".join(targets),
            )
        elif channel.type == ChannelType.KAKAO:
            # Placeholder for future Kakao integration
            pass
