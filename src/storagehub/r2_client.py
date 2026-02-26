import logging
import os
from functools import lru_cache

from django.conf import settings

try:
    import boto3
    from botocore.client import Config as BotoConfig
except Exception:  # pragma: no cover
    boto3 = None
    BotoConfig = None


logger = logging.getLogger(__name__)


def is_r2_enabled() -> bool:
    backend = str(getattr(settings, "STORAGE_BACKEND", "auto") or "auto").lower()
    if backend == "local":
        return False
    required = [
        getattr(settings, "R2_ACCOUNT_ID", ""),
        getattr(settings, "R2_ACCESS_KEY_ID", ""),
        getattr(settings, "R2_SECRET_ACCESS_KEY", ""),
        getattr(settings, "R2_BUCKET_NAME", ""),
    ]
    return bool(boto3 and all(required))


@lru_cache(maxsize=1)
def get_r2_s3_client():
    if not is_r2_enabled():
        return None
    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        service_name="s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def r2_put_fileobj(fileobj, key: str, content_type: str = "") -> dict:
    client = get_r2_s3_client()
    if client is None:
        raise RuntimeError("R2 client is not configured")
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    client.upload_fileobj(fileobj, settings.R2_BUCKET_NAME, key, ExtraArgs=extra)
    return {"bucket": settings.R2_BUCKET_NAME, "key": key}


def _safe_filename(name: str) -> str:
    raw = os.path.basename(str(name or "").strip())
    if not raw:
        return "download.bin"
    return "".join(ch if ch.isascii() and (ch.isalnum() or ch in "._- ") else "_" for ch in raw).strip() or "download.bin"


def r2_generate_get_url(key: str, expires: int = None, filename: str = "") -> str:
    client = get_r2_s3_client()
    if client is None:
        raise RuntimeError("R2 client is not configured")
    ttl = int(expires or getattr(settings, "PRESIGNED_EXPIRES_SECONDS", 600))
    params = {"Bucket": settings.R2_BUCKET_NAME, "Key": key}
    if filename:
        safe = _safe_filename(filename)
        params["ResponseContentDisposition"] = f'attachment; filename="{safe}"'
    return client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=ttl,
    )


def r2_head(key: str):
    client = get_r2_s3_client()
    if client is None:
        raise RuntimeError("R2 client is not configured")
    return client.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)


def r2_delete(key: str):
    client = get_r2_s3_client()
    if client is None:
        return
    try:
        client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except Exception as exc:
        logger.warning("R2 delete failed key=%s error=%s", key, exc)
