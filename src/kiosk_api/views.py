import logging
import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from packaging.version import InvalidVersion, Version
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from audit.service import log_event
from coupons.service import normalize_coupon_code, quote_coupon, redeem_coupon_atomic
from configs.service import get_effective_config
from core.models import Device
from mediahub.models import ShareSession
from ota.models import AppRelease
from sales.models import SaleTransaction
from storagehub.models import UploadKind
from storagehub.service import register_asset

from .auth import DeviceTokenAuthentication
from .models import DeviceHeartbeat
from .serializers import (
    ConfigAppliedSerializer,
    CouponCheckSerializer,
    HeartbeatSerializer,
    SaleCompleteSerializer,
    ShareFinalizeSerializer,
    ShareCompleteSerializer,
    ShareCreateSerializer,
    ShareUploadFileSerializer,
    ShareUploadInitSerializer,
)

logger = logging.getLogger(__name__)


def _safe_version(v: str) -> Version:
    try:
        return Version(v)
    except InvalidVersion:
        return Version("0.0.0")


_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{6,128}$")


def _blocked_if_locked(device: Device):
    if not device or not getattr(device, "is_locked", False):
        return None
    payload = {
        "ok": False,
        "reason": "DEVICE_LOCKED",
        "detail": "Device is locked by admin",
        "locked": True,
    }
    if getattr(device, "lock_reason", ""):
        payload["lock_reason"] = device.lock_reason
    if getattr(device, "locked_at", None):
        payload["locked_at"] = device.locked_at
    return Response(payload, status=423)


class AuthTokenView(TokenObtainPairView):
    permission_classes = [AllowAny]


class AuthRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class HeartbeatView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)

        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        device.last_seen_at = timezone.now()
        if payload.get("app_version"):
            device.last_app_version = payload.get("app_version")
        device.last_health_json = payload
        device.save(update_fields=["last_seen_at", "last_app_version", "last_health_json", "updated_at"])

        heartbeat = DeviceHeartbeat.objects.create(
            device=device,
            payload=payload,
            internet_ok=payload.get("internet_ok"),
            camera_ok=payload.get("camera_ok"),
            printer_ok=payload.get("printer_ok"),
        )
        return Response({"ok": True, "heartbeat_id": heartbeat.id})


class ConfigView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)

        config, version_tag = get_effective_config(device)
        return Response({"config_version": version_tag, "config": config})


class ConfigAppliedView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)

        serializer = ConfigAppliedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = serializer.validated_data["config_version"]
        applied_at = serializer.validated_data.get("applied_at") or timezone.now()

        device.last_config_version_applied = version
        device.last_config_applied_at = applied_at
        device.save(update_fields=["last_config_version_applied", "last_config_applied_at", "updated_at"])
        return Response({"ok": True, "applied_at": applied_at})


class UpdateCheckView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)

        platform = request.query_params.get("platform", "win")
        current = request.query_params.get("current", "0.0.0")
        current_v = _safe_version(current)

        active = AppRelease.objects.filter(platform=platform, is_active=True).order_by("-created_at").first()
        if not active:
            return Response(
                {
                    "platform": platform,
                    "active_version": None,
                    "min_supported_version": None,
                    "force_below_min": False,
                    "update_available": False,
                    "force_update": False,
                    "target_version": None,
                    "download_url": None,
                    "sha256": None,
                    "notes": "",
                }
            )

        active_v = _safe_version(active.version)
        min_v = _safe_version(active.min_supported_version or "0.0.0")

        update_available = current_v != active_v
        force_update = bool(active.force_below_min and current_v < min_v)
        download_url = request.build_absolute_uri(active.artifact.url) if active.artifact else None

        return Response(
            {
                "platform": platform,
                "active_version": active.version,
                "min_supported_version": active.min_supported_version,
                "force_below_min": active.force_below_min,
                "update_available": update_available,
                "force_update": force_update,
                "target_version": active.version,
                "download_url": download_url,
                "sha256": active.sha256,
                "notes": active.notes,
            }
        )


class ShareCreateView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = ShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data.get("session_id", "")

        session = ShareSession.create_24h(device=device, assets={"session_id": session_id} if session_id else {})
        share_url = request.build_absolute_uri(f"/s/{session.token}/")
        logger.info("[SHARE] create token=%s device=%s", session.token, device.device_code)
        return Response({"ok": True, "token": session.token, "share_url": share_url, "expires_at": session.expires_at})


class ShareInitUploadView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = ShareUploadInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data.get("session_id", "")
        requested_token = (serializer.validated_data.get("token") or "").strip()

        if requested_token and not _TOKEN_RE.match(requested_token):
            return Response({"ok": False, "reason": "INVALID_TOKEN_FORMAT"}, status=400)

        expires_at = timezone.now() + timedelta(hours=int(getattr(settings, "SHARE_TOKEN_TTL_HOURS", 24)))
        assets = {"kiosk_session_id": session_id} if session_id else {}

        if requested_token:
            session, created = ShareSession.objects.get_or_create(
                token=requested_token,
                defaults={
                    "device": device,
                    "created_at": timezone.now(),
                    "expires_at": expires_at,
                    "status": ShareSession.STATUS_INIT,
                    "files": {},
                    "assets": assets,
                },
            )
            if not created and session.device_id != device.id:
                return Response({"ok": False, "reason": "TOKEN_CONFLICT"}, status=409)
            if not created:
                session.expires_at = expires_at
                session.status = ShareSession.STATUS_INIT
                session.files = {}
                session.assets = assets
                session.save(update_fields=["expires_at", "status", "files", "assets"])
        else:
            session = ShareSession.create_24h(device=device, assets=assets)
            session.expires_at = expires_at
            session.status = ShareSession.STATUS_INIT
            session.files = {}
            session.save(update_fields=["expires_at", "status", "files"])

        share_url = request.build_absolute_uri(f"/s/{session.token}/")

        log_event(
            actor_user=None,
            actor_device=device,
            action="share.init",
            target_type="ShareSession",
            target_id=session.token,
            before=None,
            after={"expires_at": session.expires_at.isoformat()},
            meta={"session_id": session_id},
            ip=request.META.get("REMOTE_ADDR"),
        )
        logger.info("[SHARE] init token=%s device=%s expires_at=%s", session.token, device.device_code, session.expires_at)
        return Response({"ok": True, "token": session.token, "share_url": share_url, "expires_at": session.expires_at})


class ShareUploadFileView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = ShareUploadFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        kind = serializer.validated_data["kind"]
        upload_file = serializer.validated_data["file"]

        session = ShareSession.objects.filter(token=token, device=device).first()
        if not session:
            return Response({"detail": "Invalid token"}, status=404)
        if session.is_expired():
            return Response({"detail": "Expired"}, status=410)

        content_type = getattr(upload_file, "content_type", "") or ""
        try:
            asset, _ = register_asset(
                share=session,
                device=device,
                kind=kind,
                django_file=upload_file,
                content_type=content_type,
                request=request,
            )
        except Exception as exc:
            logger.exception("[SHARE] upload failed token=%s kind=%s error=%s", token, kind, exc)
            return Response({"ok": False, "reason": "UPLOAD_FAILED", "detail": str(exc)}, status=500)

        kind_lower = kind.lower()
        file_meta = {
            "key": asset.object_key or (asset.file.name if asset.file else ""),
            "filename": asset.original_filename or getattr(upload_file, "name", ""),
            "size": asset.size_bytes,
            "content_type": asset.content_type,
            "storage": asset.storage_backend,
        }

        files = dict(session.files or {})
        if kind == UploadKind.ORIGINAL:
            originals = list(files.get("original") or [])
            originals.append(file_meta)
            files["original"] = originals
        else:
            files[kind_lower] = file_meta
        session.files = files
        session.status = ShareSession.STATUS_UPLOADING

        assets = dict(session.assets or {})
        if kind == UploadKind.PRINT:
            assets["print_key"] = file_meta["key"]
        elif kind == UploadKind.FRAME:
            assets["frame_key"] = file_meta["key"]
        elif kind == UploadKind.GIF:
            assets["gif_key"] = file_meta["key"]
        elif kind == UploadKind.VIDEO:
            assets["video_key"] = file_meta["key"]
        elif kind == UploadKind.ORIGINAL:
            original_keys = list(assets.get("original_keys") or [])
            original_keys.append(file_meta["key"])
            assets["original_keys"] = original_keys
        session.assets = assets
        session.save(update_fields=["files", "assets", "status"])

        log_event(
            actor_user=None,
            actor_device=device,
            action="share.upload",
            target_type="ShareSession",
            target_id=session.token,
            before=None,
            after={"kind": kind, "key": file_meta["key"]},
            meta={"kind": kind, "size_bytes": asset.size_bytes, "content_type": asset.content_type, "storage": asset.storage_backend},
            ip=request.META.get("REMOTE_ADDR"),
        )
        logger.info(
            "[SHARE] upload token=%s kind=%s key=%s size=%s storage=%s",
            token,
            kind,
            file_meta["key"],
            asset.size_bytes,
            asset.storage_backend,
        )
        return Response({"ok": True, "token": token, "kind": kind_lower, "key": file_meta["key"], "size_bytes": asset.size_bytes})


class ShareFinalizeView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = ShareFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        meta = serializer.validated_data.get("meta") or {}

        session = ShareSession.objects.filter(token=token, device=device).first()
        if not session:
            return Response({"detail": "Invalid token"}, status=404)
        if session.is_expired():
            return Response({"detail": "Expired"}, status=410)

        assets = dict(session.assets or {})
        if meta:
            assets["meta"] = meta
        session.assets = assets
        session.status = ShareSession.STATUS_FINALIZED
        session.save(update_fields=["assets", "status"])

        share_url = request.build_absolute_uri(f"/s/{session.token}/")
        snapshot = dict(session.assets or {})

        log_event(
            actor_user=None,
            actor_device=device,
            action="share.finalize",
            target_type="ShareSession",
            target_id=session.token,
            before=None,
            after={"share_url": share_url},
            meta={"asset_keys": sorted(snapshot.keys())},
            ip=request.META.get("REMOTE_ADDR"),
        )
        logger.info("[SHARE] finalize token=%s device=%s", token, device.device_code)
        return Response({"ok": True, "url": f"/s/{session.token}/", "share_url": share_url, "assets": snapshot})


class ShareCompleteView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = ShareCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        assets = serializer.validated_data["assets"]

        session = ShareSession.objects.filter(token=token, device=device).first()
        if not session:
            return Response({"detail": "Invalid token"}, status=404)
        if session.is_expired():
            return Response({"detail": "Expired"}, status=410)

        session.assets = assets
        session.status = ShareSession.STATUS_FINALIZED
        session.save(update_fields=["assets", "status"])
        logger.info("[SHARE] complete token=%s device=%s", token, device.device_code)
        return Response({"ok": True})


class CouponCheckView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = CouponCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code_raw = serializer.validated_data["coupon_code"]
        amount_due = serializer.validated_data["amount_due"]

        try:
            normalized = normalize_coupon_code(code_raw)
        except ValueError:
            return Response(
                {
                    "ok": True,
                    "valid": False,
                    "normalized_code": None,
                    "coupon_amount": 0,
                    "remaining_due": int(amount_due),
                    "expires_at": None,
                    "reason": "INVALID_FORMAT",
                }
            )

        valid, coupon_amount, remaining_due, reason, coupon = quote_coupon(normalized, amount_due)
        return Response(
            {
                "ok": True,
                "valid": bool(valid),
                "normalized_code": normalized,
                "coupon_amount": int(coupon_amount),
                "remaining_due": int(remaining_due),
                "expires_at": coupon.expires_at if coupon else None,
                "reason": reason,
            }
        )


class SaleCompleteView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        device: Device = getattr(request, "device", None)
        if not device:
            return Response({"detail": "Device auth required"}, status=401)
        blocked = _blocked_if_locked(device)
        if blocked:
            return blocked

        serializer = SaleCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_id = str(data["session_id"])
        existing = SaleTransaction.objects.filter(device=device, session_id=session_id).select_related("coupon").first()
        if existing:
            log_event(
                actor_user=None,
                actor_device=device,
                action="sale.complete",
                target_type="SaleTransaction",
                target_id=str(existing.pk),
                before=None,
                after={
                    "session_id": existing.session_id,
                    "layout_id": existing.layout_id,
                    "price_total": existing.price_total,
                    "payment_method": existing.payment_method,
                },
                meta={"created": False, "already_exists": True},
                ip=request.META.get("REMOTE_ADDR"),
            )
            return Response(
                {
                    "ok": True,
                    "sale_id": existing.id,
                    "created": False,
                    "already_exists": True,
                    "sale": {
                        "session_id": existing.session_id,
                        "layout_id": existing.layout_id,
                        "price_total": existing.price_total,
                        "payment_method": existing.payment_method,
                    },
                }
            )

        method = str(data["payment_method"]).upper()
        valid_methods = {x for x, _ in SaleTransaction.PAYMENT_CHOICES}
        if method not in valid_methods:
            return Response({"ok": False, "reason": "INVALID_PAYMENT_METHOD"}, status=400)

        price_total = int(data["price_total"])
        amount_cash = int(data.get("amount_cash", 0))
        amount_coupon = int(data.get("amount_coupon", 0))
        coupon_code = (data.get("coupon_code") or "").strip()

        if amount_cash + amount_coupon != price_total:
            return Response({"ok": False, "reason": "AMOUNT_SUM_MISMATCH"}, status=400)

        coupon_obj = None
        if method in (SaleTransaction.METHOD_COUPON, SaleTransaction.METHOD_COUPON_CASH):
            if not coupon_code:
                return Response({"ok": False, "reason": "COUPON_REQUIRED"}, status=400)
            try:
                coupon_obj = redeem_coupon_atomic(
                    device=device,
                    code=coupon_code,
                    session_id=session_id,
                    amount_due=price_total,
                    amount_coupon_expected=amount_coupon,
                )
            except ValueError as exc:
                return Response({"ok": False, "reason": str(exc)}, status=400)
        else:
            if amount_coupon != 0:
                return Response({"ok": False, "reason": "INVALID_COUPON_AMOUNT_FOR_METHOD"}, status=400)

        try:
            with transaction.atomic():
                sale, created = SaleTransaction.objects.get_or_create(
                    device=device,
                    session_id=session_id,
                    defaults={
                        "org": device.org,
                        "branch": device.branch,
                        "layout_id": str(data["layout_id"]),
                        "prints": int(data.get("prints", 2)),
                        "currency": str(data.get("currency", "KRW")),
                        "price_total": price_total,
                        "payment_method": method,
                        "amount_cash": amount_cash,
                        "amount_coupon": amount_coupon,
                        "coupon": coupon_obj,
                        "meta": data.get("meta", {}),
                    },
                )
        except IntegrityError:
            sale = SaleTransaction.objects.filter(device=device, session_id=session_id).select_related("coupon").first()
            created = False

        log_event(
            actor_user=None,
            actor_device=device,
            action="sale.complete",
            target_type="SaleTransaction",
            target_id=str(sale.pk),
            before=None,
            after={
                "session_id": sale.session_id,
                "layout_id": sale.layout_id,
                "price_total": sale.price_total,
                "payment_method": sale.payment_method,
            },
            meta={"created": created},
            ip=request.META.get("REMOTE_ADDR"),
        )

        return Response(
            {
                "ok": True,
                "sale_id": sale.id,
                "created": bool(created),
                "already_exists": not bool(created),
                "sale": {
                    "session_id": sale.session_id,
                    "layout_id": sale.layout_id,
                    "prints": sale.prints,
                    "currency": sale.currency,
                    "price_total": sale.price_total,
                    "payment_method": sale.payment_method,
                    "amount_cash": sale.amount_cash,
                    "amount_coupon": sale.amount_coupon,
                    "coupon_code": sale.coupon.formatted_code if sale.coupon else None,
                },
            }
        )
