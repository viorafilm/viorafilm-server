import hashlib
import hmac

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from core.models import Device

from .principals import DevicePrincipal


class DeviceTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        code = request.headers.get("X-Device-Code")
        token = request.headers.get("X-Device-Token")
        if not code or not token:
            return None

        device = Device.objects.filter(device_code=code, is_active=True).first()
        if not device or not device.token_hash:
            raise exceptions.AuthenticationFailed("Invalid device")

        hashed = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(hashed, device.token_hash):
            raise exceptions.AuthenticationFailed("Invalid token")

        request.device = device
        return DevicePrincipal(device), None

