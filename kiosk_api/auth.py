import hashlib
import hmac
from dataclasses import dataclass

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.models import Device


@dataclass
class DevicePrincipal:
    device: Device

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def username(self) -> str:
        return f"device:{self.device.device_code}"


class DeviceTokenAuthentication(BaseAuthentication):
    header_code = "X-Device-Code"
    header_token = "X-Device-Token"

    def authenticate_header(self, _request) -> str:
        return self.header_token

    def authenticate(self, request):
        device_code = (request.headers.get(self.header_code) or "").strip()
        raw_token = (request.headers.get(self.header_token) or "").strip()
        if not device_code or not raw_token:
            raise AuthenticationFailed("Missing device credentials.")

        try:
            device = Device.objects.select_related("org", "branch").get(
                device_code=device_code,
                is_active=True,
            )
        except Device.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid device credentials.") from exc

        if not device.token_hash:
            raise AuthenticationFailed("Device token is not provisioned.")

        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(device.token_hash, token_hash):
            raise AuthenticationFailed("Invalid device credentials.")

        setattr(request, "device", device)
        setattr(request._request, "device", device)
        return DevicePrincipal(device=device), device
