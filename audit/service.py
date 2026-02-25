from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from core.models import Device

from .models import AuditEvent


def log_event(
    actor_user,
    action: str,
    target_type: str,
    target_id: str,
    before: Any = None,
    after: Any = None,
    meta: dict[str, Any] | None = None,
    actor_device: Device | None = None,
    ip: str | None = None,
) -> AuditEvent:
    user_model = get_user_model()
    safe_actor_user = actor_user if isinstance(actor_user, user_model) else None
    safe_actor_device = actor_device if isinstance(actor_device, Device) else None
    payload_meta = meta if isinstance(meta, dict) else {}
    return AuditEvent.objects.create(
        actor_user=safe_actor_user,
        actor_device=safe_actor_device,
        action=str(action or "")[:120],
        target_type=str(target_type or "")[:120],
        target_id=str(target_id or "")[:120],
        before=before,
        after=after,
        meta=payload_meta,
        ip=(str(ip).strip()[:64] if ip else None),
    )
