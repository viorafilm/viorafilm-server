from __future__ import annotations

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import send_mail


def send_slack(webhook: str, text: str) -> bool:
    hook = (webhook or "").strip()
    if not hook:
        return False
    payload = {"text": text}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        hook,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= int(getattr(resp, "status", 500)) < 300
    except (urllib.error.URLError, ValueError, TimeoutError):
        return False


def send_email(to: str | list[str], subject: str, body: str) -> bool:
    recipients: list[str] = []
    if isinstance(to, list):
        recipients = [str(x).strip() for x in to if str(x).strip()]
    elif isinstance(to, str):
        recipients = [x.strip() for x in to.split(",") if x.strip()]
    if not recipients:
        return False

    sent = send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@photoharu.local"),
        recipient_list=recipients,
        fail_silently=True,
    )
    return bool(sent)

