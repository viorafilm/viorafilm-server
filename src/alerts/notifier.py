import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

from core.models import Device

from .models import ChannelType, NotificationChannel


def _channels_for_device(device: Device):
    queryset = NotificationChannel.objects.filter(enabled=True).filter(Q(org=device.org) | Q(org__isnull=True))
    return list(queryset)


def notify(device: Device, title: str, text: str):
    channels = _channels_for_device(device)
    for channel in channels:
        if channel.type == ChannelType.SLACK:
            webhook = channel.config.get("webhook_url")
            if webhook:
                try:
                    requests.post(webhook, json={"text": f"{title}\n{text}"}, timeout=5)
                except Exception:
                    pass
        elif channel.type == ChannelType.EMAIL:
            target = channel.config.get("to")
            if target:
                try:
                    send_mail(title, text, settings.DEFAULT_FROM_EMAIL, [target], fail_silently=True)
                except Exception:
                    pass
        elif channel.type == ChannelType.KAKAO:
            # Placeholder for future Kakao integration
            pass
