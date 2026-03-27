from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserRole
from core.models import Branch, Device, Organization
from kiosk_api.models import DeviceRuntimeLog
from sales.models import SaleTransaction

from .views import REMOTE_ACTION_KIND_OFFLINE_GUARD_RESET, _build_device_rows
from .views import _resolve_sale_payment_breakdown, _resolve_sale_payment_method_label


class SalePaymentBreakdownTests(SimpleTestCase):
    def test_card_payment_shows_card_amount_only(self):
        sale = SaleTransaction(
            payment_method=SaleTransaction.METHOD_CARD,
            price_total=7000,
            amount_cash=7000,
            amount_coupon=0,
            meta={"kiosk_payment_selection": "card"},
        )
        self.assertEqual(_resolve_sale_payment_breakdown(sale), {"cash": 0, "card": 7000, "coupon": 0})
        self.assertEqual(_resolve_sale_payment_method_label(sale), "CARD")

    def test_coupon_card_payment_moves_remainder_to_card(self):
        sale = SaleTransaction(
            payment_method=SaleTransaction.METHOD_COUPON_CASH,
            price_total=10000,
            amount_cash=4000,
            amount_coupon=6000,
            meta={"kiosk_payment_selection": "card"},
        )
        self.assertEqual(_resolve_sale_payment_breakdown(sale), {"cash": 0, "card": 4000, "coupon": 6000})
        self.assertEqual(_resolve_sale_payment_method_label(sale), "COUPON + CARD")


class DeviceUnlockGraceTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Org", code="org")
        self.branch = Branch.objects.create(org=self.org, name="Branch", code="branch")
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="pw",
            is_staff=True,
            is_superuser=True,
            role=UserRole.SUPERADMIN,
        )

    def _create_device(self, code: str, **overrides) -> Device:
        payload = {
            "org": self.org,
            "branch": self.branch,
            "device_code": code,
            "is_active": True,
        }
        payload.update(overrides)
        return Device.objects.create(**payload)

    @override_settings(
        DEVICE_AUTO_LOCK_ENABLED=True,
        DEVICE_AUTO_LOCK_OFFLINE_DAYS=3,
        SECURE_SSL_REDIRECT=False,
    )
    def test_unlock_device_resets_manual_offline_grace(self):
        device = self._create_device(
            "dev-unlock",
            is_locked=True,
            lock_reason="AUTO_LOCK_OFFLINE_3D",
            locked_at=timezone.now() - timedelta(minutes=10),
            last_seen_at=timezone.now() - timedelta(days=4),
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard_devices"),
            {
                "action": "unlock_device",
                "device_id": str(device.id),
            },
        )

        self.assertIn(response.status_code, (301, 302))
        device.refresh_from_db()
        self.assertFalse(device.is_locked)
        self.assertEqual(device.lock_reason, "")
        self.assertIsNone(device.locked_at)
        self.assertIsNotNone(device.offline_unlock_grace_until)
        self.assertEqual(device.pending_remote_action.get("kind"), REMOTE_ACTION_KIND_OFFLINE_GUARD_RESET)
        remaining_seconds = int((device.offline_unlock_grace_until - timezone.now()).total_seconds())
        self.assertGreater(remaining_seconds, 2 * 86400 + 23 * 3600)
        self.assertLessEqual(remaining_seconds, 3 * 86400)

    @override_settings(
        DEVICE_AUTO_LOCK_ENABLED=True,
        DEVICE_AUTO_LOCK_OFFLINE_DAYS=3,
        SECURE_SSL_REDIRECT=False,
    )
    def test_build_device_rows_prefers_unlock_grace_remaining(self):
        device = self._create_device(
            "dev-rows",
            last_seen_at=timezone.now() - timedelta(days=4),
            last_health_json={
                "offline_guard_enabled": True,
                "offline_grace_remaining_seconds": -300,
            },
        )
        device.offline_unlock_grace_until = timezone.now() + timedelta(days=3)
        device.pending_remote_action = {
            "id": "pending-1",
            "kind": REMOTE_ACTION_KIND_OFFLINE_GUARD_RESET,
        }
        device.save(update_fields=["offline_unlock_grace_until", "pending_remote_action", "updated_at"])

        rows = _build_device_rows(self.user, devices_qs=Device.objects.filter(id=device.id))

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertGreater(int(row["offline_grace_remaining_seconds"]), 2 * 86400 + 23 * 3600)
        self.assertFalse(bool(row["offline_grace_overdue"]))
        self.assertTrue(bool(row["offline_unlock_pending"]))


class SalesPaginationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Org", code="org")
        self.branch = Branch.objects.create(org=self.org, name="Branch", code="branch")
        self.device = Device.objects.create(org=self.org, branch=self.branch, device_code="dev-sales")
        self.user = get_user_model().objects.create_user(
            username="salesadmin",
            password="pw",
            is_staff=True,
            is_superuser=True,
            role=UserRole.SUPERADMIN,
        )

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_sales_view_defaults_to_ten_rows_and_supports_per_page(self):
        for idx in range(12):
            SaleTransaction.objects.create(
                org=self.org,
                branch=self.branch,
                device=self.device,
                session_id=f"s-{idx}",
                layout_id="test",
                prints=2,
                currency="KRW",
                price_total=4000,
                payment_method=SaleTransaction.METHOD_CASH,
                amount_cash=4000,
                amount_coupon=0,
            )

        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard_sales"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["per_page"], 10)
        self.assertEqual(len(response.context["sales"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 12)

        response = self.client.get(reverse("dashboard_sales"), {"per_page": 20})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["per_page"], 20)
        self.assertEqual(len(response.context["sales"]), 12)

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_sales_view_filters_by_payment_method(self):
        SaleTransaction.objects.create(
            org=self.org,
            branch=self.branch,
            device=self.device,
            session_id="cash-1",
            layout_id="test",
            prints=2,
            currency="KRW",
            price_total=4000,
            payment_method=SaleTransaction.METHOD_CASH,
            amount_cash=4000,
            amount_coupon=0,
        )
        SaleTransaction.objects.create(
            org=self.org,
            branch=self.branch,
            device=self.device,
            session_id="card-1",
            layout_id="test",
            prints=2,
            currency="KRW",
            price_total=4000,
            payment_method=SaleTransaction.METHOD_CARD,
            amount_cash=4000,
            amount_coupon=0,
            meta={"kiosk_payment_selection": "card"},
        )

        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard_sales"), {"payment_filter": "card"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["payment_filter"], "card")
        self.assertEqual(len(response.context["sales"]), 1)
        self.assertEqual(response.context["sales"][0].session_id, "card-1")


class DeviceLogsViewTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Org", code="org")
        self.branch = Branch.objects.create(org=self.org, name="Branch", code="branch")
        self.device = Device.objects.create(
            org=self.org,
            branch=self.branch,
            device_code="dev-log",
        )
        self.user = get_user_model().objects.create_user(
            username="logadmin",
            password="pw",
            is_staff=True,
            is_superuser=True,
            role=UserRole.SUPERADMIN,
        )
        DeviceRuntimeLog.objects.create(
            device=self.device,
            log_filename="kiosk_20260327.log",
            chunk_start=0,
            chunk_end=5,
            content="alpha\n",
        )
        DeviceRuntimeLog.objects.create(
            device=self.device,
            log_filename="kiosk_20260327.log",
            chunk_start=6,
            chunk_end=10,
            content="beta\n",
        )

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_device_logs_view_renders_last_reported_excerpt(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard_device_logs", args=[self.device.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kiosk_20260327.log")
        self.assertContains(response, "alpha")
        self.assertContains(response, "beta")
