import os
import re
import uuid
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import UploadAsset
from .r2_client import is_r2_enabled, r2_delete, r2_generate_get_url, r2_put_fileobj


def _safe_text(text: str, fallback: str = "file") -> str:
    value = re.sub(r"[^A-Za-z0-9._-]", "_", str(text or "")).strip("._")
    return value or fallback


def normalize_kind(kind: str) -> str:
    return _safe_text(kind, fallback="unknown").upper()


def build_object_key(token: str, kind: str, filename: str) -> str:
    prefix = _safe_text(getattr(settings, "R2_PREFIX", "sessions"), fallback="sessions")
    safe_token = _safe_text(token, fallback=uuid.uuid4().hex)
    safe_kind = normalize_kind(kind).lower()
    safe_name = _safe_text(os.path.basename(filename or "upload.bin"), fallback="upload.bin")
    stamp = timezone.now().strftime("%Y%m%dT%H%M%S")
    rand = uuid.uuid4().hex[:8]
    return f"{prefix}/{safe_token}/{safe_kind}/{stamp}_{rand}_{safe_name}"


def build_absolute_file_url(request, relative_path: str) -> str:
    if not relative_path:
        return ""
    rel_url = f"{settings.MEDIA_URL.rstrip('/')}/{relative_path.lstrip('/')}"
    if request is not None:
        return request.build_absolute_uri(rel_url)
    base = getattr(settings, "PUBLIC_BASE_URL", "")
    if base:
        return urljoin(base.rstrip("/") + "/", rel_url.lstrip("/"))
    return rel_url


def generate_download_url_from_meta(meta: dict, request=None, expires=None, filename: str = "") -> str:
    if not isinstance(meta, dict):
        return ""
    key = meta.get("key") or ""
    storage = (meta.get("storage") or "").lower()
    file_name = str(filename or meta.get("filename") or os.path.basename(str(key)))
    if not key:
        return ""
    if storage == "r2":
        return r2_generate_get_url(
            key,
            expires=int(expires or settings.PRESIGNED_EXPIRES_SECONDS),
            filename=file_name,
        )
    return build_absolute_file_url(request, key)


def delete_by_meta(meta: dict):
    if not isinstance(meta, dict):
        return
    key = meta.get("key") or ""
    storage = (meta.get("storage") or "").lower()
    if not key:
        return
    if storage == "r2":
        r2_delete(key)
        return
    try:
        default_storage.delete(key)
    except Exception:
        pass


def delete_asset_blob(asset: UploadAsset):
    if (asset.storage_backend or "").lower() == "r2":
        if asset.object_key:
            r2_delete(asset.object_key)
        return
    if asset.file:
        try:
            asset.file.delete(save=False)
        except Exception:
            pass


def register_asset(*, share, device, kind: str, django_file, content_type: str = "", request=None):
    filename = getattr(django_file, "name", "upload.bin")
    key = build_object_key(share.token, kind, filename)
    size_bytes = getattr(django_file, "size", 0) or 0
    ctype = content_type or ""

    if is_r2_enabled():
        if hasattr(django_file, "seek"):
            django_file.seek(0)
        r2_put_fileobj(django_file, key, ctype)
        asset = UploadAsset.objects.create(
            device=device,
            share=share,
            kind=kind,
            storage_backend="r2",
            object_key=key,
            original_filename=os.path.basename(filename),
            content_type=ctype,
            size_bytes=size_bytes,
        )
        url = r2_generate_get_url(key, int(getattr(settings, "PRESIGNED_EXPIRES_SECONDS", 600)))
        return asset, url

    if hasattr(django_file, "seek"):
        django_file.seek(0)
    saved_path = default_storage.save(key, File(django_file))

    asset = UploadAsset.objects.create(
        device=device,
        share=share,
        kind=kind,
        storage_backend="local",
        object_key=saved_path,
        original_filename=os.path.basename(filename),
        content_type=ctype,
        size_bytes=size_bytes,
    )
    asset.file.name = saved_path
    asset.save(update_fields=["file"])
    url = build_absolute_file_url(request, saved_path)
    return asset, url
