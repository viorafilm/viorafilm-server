import hashlib
import hmac

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.utils import timezone

from core.models import Device

from .principals import DevicePrincipal


class DeviceTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        code = request.headers.get("X-Device-Code")
        token = request.headers.get("X-Device-Token")
        install_key = str(request.headers.get("X-Device-Install-Key") or "").strip()
        if not code or not token:
            return None

        device = Device.objects.filter(device_code=code, is_active=True).first()
        if not device or not device.token_hash:
            raise exceptions.AuthenticationFailed("Invalid device")

        hashed = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(hashed, device.token_hash):
            raise exceptions.AuthenticationFailed("Invalid token")

        if device.install_key_hash:
            if not install_key:
                raise exceptions.AuthenticationFailed("Install binding required")
            if not device.verify_install_key(install_key):
                raise exceptions.AuthenticationFailed("Token already bound to another installation")
            now = timezone.now()
            if (
                device.last_install_seen_at is None
                or abs((now - device.last_install_seen_at).total_seconds()) >= 300.0
            ):
                device.last_install_seen_at = now
                device.save(update_fields=["last_install_seen_at", "updated_at"])
        elif install_key:
            device.bind_install_key(install_key)

        request.device = device
        return DevicePrincipal(device), None
