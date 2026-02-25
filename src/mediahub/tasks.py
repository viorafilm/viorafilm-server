from celery import shared_task
from django.utils import timezone

from storagehub.models import UploadAsset
from storagehub.service import delete_asset_blob, delete_by_meta

from .models import ShareSession


@shared_task
def cleanup_expired_shares():
    now = timezone.now()
    expired_sessions = ShareSession.objects.filter(expires_at__lte=now)

    for session in expired_sessions.iterator():
        uploads = UploadAsset.objects.filter(share=session)
        for asset in uploads.iterator():
            delete_asset_blob(asset)
        uploads.delete()

        files = dict(session.files or {})
        for k, meta in files.items():
            if isinstance(meta, list):
                for m in meta:
                    delete_by_meta(m)
            else:
                delete_by_meta(meta)

        old_assets = dict(session.assets or {})
        assets = dict(old_assets)
        assets["expired"] = True
        assets.pop("print_url", None)
        assets.pop("frame_url", None)
        assets.pop("gif_url", None)
        assets.pop("video_url", None)
        assets.pop("original_urls", None)
        changed_fields = []
        if assets != old_assets:
            session.assets = assets
            changed_fields.append("assets")
        if session.files:
            session.files = {}
            changed_fields.append("files")
        if changed_fields:
            session.save(update_fields=changed_fields)
