from core.models import Device


class DevicePrincipal:
    def __init__(self, device: Device):
        self.device = device

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"DevicePrincipal({self.device.device_code})"

