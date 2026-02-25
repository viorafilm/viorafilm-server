from typing import Any, Dict, Optional

from accounts.models import User
from core.models import Device

from .models import AuditEvent


def log_event(
    *,
    actor_user: Optional[User],
    actor_device: Optional[Device],
    action: str,
    target_type: str,
    target_id: str,
    before: Any = None,
    after: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        actor_user=actor_user,
        actor_device=actor_device,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        before=before,
        after=after,
        meta=meta or {},
        ip=ip,
    )

