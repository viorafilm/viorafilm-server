from __future__ import annotations

from typing import Any

from django.db.models import F
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kiosk_api.auth import DevicePrincipal, DeviceTokenAuthentication

from .models import ShareSession, generate_share_token


def _get_authenticated_device(request):
    device = getattr(request, "device", None)
    if device is None and isinstance(request.user, DevicePrincipal):
        device = request.user.device
    return device


class KioskShareCreateAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"detail": "Invalid payload. JSON object required."}, status=status.HTTP_400_BAD_REQUEST)

        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            return Response({"detail": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        device = _get_authenticated_device(request)
        if device is None:
            return Response({"detail": "Device auth context missing."}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_share_token()
        share = ShareSession.objects.create(
            token=token,
            device=device,
            assets={"session_id": session_id},
        )

        share_path = reverse("mediahub-share-page", kwargs={"token": token})
        share_url = request.build_absolute_uri(share_path)
        return Response(
            {
                "share_url": share_url,
                "token": token,
                "expires_at": share.expires_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class KioskShareCompleteAPIView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data
        if not isinstance(payload, dict):
            return Response({"detail": "Invalid payload. JSON object required."}, status=status.HTTP_400_BAD_REQUEST)

        token = str(payload.get("token", "")).strip()
        if not token:
            return Response({"detail": "token is required."}, status=status.HTTP_400_BAD_REQUEST)

        assets = payload.get("assets", {})
        if not isinstance(assets, dict):
            return Response({"detail": "assets must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)

        device = _get_authenticated_device(request)
        if device is None:
            return Response({"detail": "Device auth context missing."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            share = ShareSession.objects.get(token=token, device=device)
        except ShareSession.DoesNotExist:
            return Response({"detail": "Share token not found."}, status=status.HTTP_404_NOT_FOUND)

        current_assets = share.assets if isinstance(share.assets, dict) else {}
        merged_assets = {**current_assets, **assets}
        share.assets = merged_assets
        share.save(update_fields=["assets"])

        return Response(
            {
                "ok": True,
                "token": share.token,
                "expires_at": share.expires_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


def _normalize_assets(raw_assets: Any) -> list[dict[str, str]]:
    if not isinstance(raw_assets, dict):
        return []
    rows: list[dict[str, str]] = []
    for key, value in raw_assets.items():
        url = None
        if isinstance(value, str):
            url = value
        elif isinstance(value, dict):
            url = value.get("url") or value.get("path")
        if not isinstance(url, str) or not url.strip():
            continue
        rows.append({"name": str(key), "url": url.strip()})
    return rows


class SharePublicPageView(View):
    template_name = "mediahub/share_page.html"

    def get(self, request, token: str):
        try:
            share = ShareSession.objects.select_related("device").get(token=token)
        except ShareSession.DoesNotExist as exc:
            raise Http404("Share link not found.") from exc

        if share.is_expired:
            raise Http404("Share link expired.")

        ShareSession.objects.filter(pk=share.pk).update(view_count=F("view_count") + 1)
        share.refresh_from_db(fields=["view_count"])

        context = {
            "token": share.token,
            "created_at": share.created_at,
            "expires_at": share.expires_at,
            "is_expired": timezone.now() >= share.expires_at,
            "assets": _normalize_assets(share.assets),
            "device_code": share.device.device_code,
        }
        return render(request, self.template_name, context)

