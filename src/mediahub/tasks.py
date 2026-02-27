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

        session.delete()
