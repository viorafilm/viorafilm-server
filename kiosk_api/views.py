from django.utils import timezone
from packaging.version import InvalidVersion, Version
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from configs.service import get_effective_config
from ota.models import AppRelease

from .auth import DevicePrincipal, DeviceTokenAuthentication
from .models import DeviceHeartbeat


def _as_optional_bool(value):
    if isinstance(value, bool):
        return value
    return None


def _derive_printer_ok(payload: dict) -> bool | None:
    direct = _as_optional_bool(payload.get("printer_ok"))
    if direct is not None:
        return direct

    values: list[bool] = []
    for key in ("printer_ds620", "printer_rx1hs"):
        item = payload.get(key)
        if isinstance(item, dict):
            val = _as_optional_bool(item.get("ok"))
            if val is not None:
                values.append(val)
    if not values:
        return None
    return any(values)


class HeartbeatAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response(
                {"detail": "Invalid payload. JSON object required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = getattr(request, "device", None)
        if device is None and isinstance(request.user, DevicePrincipal):
            device = request.user.device
        if device is None:
            return Response({"detail": "Device auth context missing."}, status=status.HTTP_401_UNAUTHORIZED)

        now = timezone.now()
        app_version_raw = payload.get("app_version")
        app_version = None
        if app_version_raw is not None:
            app_version = str(app_version_raw).strip()[:64]

        internet_ok = _as_optional_bool(payload.get("internet_ok"))
        camera_ok = _as_optional_bool(payload.get("camera_ok"))
        printer_ok = _derive_printer_ok(payload)

        device.last_seen_at = now
        if app_version:
            device.last_app_version = app_version
        device.last_health_json = payload
        device.save(update_fields=["last_seen_at", "last_app_version", "last_health_json", "updated_at"])

        DeviceHeartbeat.objects.create(
            device=device,
            payload=payload,
            internet_ok=internet_ok,
            camera_ok=camera_ok,
            printer_ok=printer_ok,
        )

        return Response(
            {
                "ok": True,
                "device_code": device.device_code,
                "received_at": now.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class KioskConfigAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        device = getattr(request, "device", None)
        if device is None and isinstance(request.user, DevicePrincipal):
            device = request.user.device
        if device is None:
            return Response({"detail": "Device auth context missing."}, status=status.HTTP_401_UNAUTHORIZED)

        config, version_tag = get_effective_config(device)
        return Response(
            {
                "config_version": version_tag,
                "config": config,
            },
            status=status.HTTP_200_OK,
        )


class KioskConfigAppliedAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response(
                {"detail": "Invalid payload. JSON object required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config_version = str(payload.get("config_version", "")).strip()
        if not config_version:
            return Response(
                {"detail": "config_version is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = getattr(request, "device", None)
        if device is None and isinstance(request.user, DevicePrincipal):
            device = request.user.device
        if device is None:
            return Response({"detail": "Device auth context missing."}, status=status.HTTP_401_UNAUTHORIZED)

        device.last_config_version_applied = config_version[:64]
        device.save(update_fields=["last_config_version_applied", "updated_at"])

        applied_at = payload.get("applied_at")
        return Response(
            {
                "ok": True,
                "device_code": device.device_code,
                "config_version": device.last_config_version_applied,
                "applied_at": applied_at,
            },
            status=status.HTTP_200_OK,
        )


class KioskUpdatesCheckAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platform = str(request.query_params.get("platform", "win")).strip().lower() or "win"
        current_text = str(request.query_params.get("current", "0.0.0")).strip() or "0.0.0"

        if platform != AppRelease.PLATFORM_WIN:
            return Response(
                {"detail": f"Unsupported platform: {platform}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active = (
            AppRelease.objects.filter(platform=platform, is_active=True)
            .order_by("-created_at", "-id")
            .first()
        )

        if active is None:
            return Response(
                {
                    "platform": platform,
                    "active_version": None,
                    "min_supported_version": None,
                    "force_below_min": False,
                    "update_available": False,
                    "force_update": False,
                    "download_url": None,
                    "sha256": None,
                    "notes": "",
                },
                status=status.HTTP_200_OK,
            )

        try:
            current_v = Version(current_text)
            active_v = Version(str(active.version))
        except InvalidVersion:
            return Response(
                {"detail": f"Invalid version format: current={current_text} active={active.version}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            min_v = Version(str(active.min_supported_version))
        except InvalidVersion:
            min_v = active_v

        update_available = current_v < active_v
        force_update = bool(active.force_below_min and current_v < min_v)

        artifact_url = None
        if getattr(active, "artifact", None):
            try:
                artifact_url = request.build_absolute_uri(active.artifact.url)
            except Exception:
                artifact_url = None

        return Response(
            {
                "platform": platform,
                "active_version": str(active.version),
                "min_supported_version": str(active.min_supported_version),
                "force_below_min": bool(active.force_below_min),
                "update_available": bool(update_available),
                "force_update": bool(force_update),
                "download_url": artifact_url,
                "sha256": active.sha256,
                "notes": active.notes or "",
            },
            status=status.HTTP_200_OK,
        )
