from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from core.models import Branch, Device, Organization

from .tasks import auto_lock_offline_devices


class AutoLockOfflineDevicesTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Org", code="org")
        self.branch = Branch.objects.create(org=self.org, name="Branch", code="branch")

    def _create_device(self, code: str) -> Device:
        return Device.objects.create(
            org=self.org,
            branch=self.branch,
            device_code=code,
            is_active=True,
            is_locked=False,
            last_seen_at=timezone.now() - timedelta(days=4),
        )

    @override_settings(DEVICE_AUTO_LOCK_ENABLED=True, DEVICE_AUTO_LOCK_OFFLINE_DAYS=3)
    def test_task_skips_device_with_active_unlock_grace(self):
        device = self._create_device("dev-skip")
        device.offline_unlock_grace_until = timezone.now() + timedelta(days=3)
        device.save(update_fields=["offline_unlock_grace_until", "updated_at"])

        auto_lock_offline_devices()

        device.refresh_from_db()
        self.assertFalse(device.is_locked)
        self.assertIsNotNone(device.offline_unlock_grace_until)

    @override_settings(DEVICE_AUTO_LOCK_ENABLED=True, DEVICE_AUTO_LOCK_OFFLINE_DAYS=3)
    def test_task_relocks_device_after_unlock_grace_expires(self):
        device = self._create_device("dev-lock")
        device.offline_unlock_grace_until = timezone.now() - timedelta(minutes=1)
        device.save(update_fields=["offline_unlock_grace_until", "updated_at"])

        auto_lock_offline_devices()

        device.refresh_from_db()
        self.assertTrue(device.is_locked)
        self.assertEqual(device.lock_reason, "AUTO_LOCK_OFFLINE_3D")
        self.assertIsNone(device.offline_unlock_grace_until)
