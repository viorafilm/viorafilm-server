import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

from core.models import Device

from .models import ChannelType, NotificationChannel


def _channels_for_device(device: Device):
    queryset = NotificationChannel.objects.filter(enabled=True).filter(Q(org=device.org) | Q(org__isnull=True))
    return list(queryset)


def _parse_email_targets(raw_value):
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
                    pass
        elif channel.type == ChannelType.EMAIL:
            targets = _parse_email_targets(channel.config.get("to"))
            if not targets:
                targets = _parse_email_targets(channel.config.get("recipients"))
            for target in targets:
                try:
                    send_mail(title, text, settings.DEFAULT_FROM_EMAIL, [target], fail_silently=True)
                except Exception:
                    pass
        elif channel.type == ChannelType.KAKAO:
            # Placeholder for future Kakao integration
            pass
