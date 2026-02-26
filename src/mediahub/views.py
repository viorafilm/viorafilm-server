import logging

from django.http import HttpResponse, HttpResponseGone
from django.shortcuts import render

from storagehub.service import generate_download_url_from_meta

from .models import ShareSession

logger = logging.getLogger(__name__)


def share_page(request, token: str):
    session = ShareSession.objects.filter(token=token).first()
    if not session:
        return HttpResponse("Not found", status=404)
    if session.is_expired():
        logger.info("[SHARE_PAGE] expired token=%s", token)
        return render(
            request,
            "mediahub/share.html",
            {"session": session, "assets": {}, "expires_at": session.expires_at, "expired": True},
            status=410,
        )
    session.view_count += 1
    session.save(update_fields=["view_count"])

    files = session.files if isinstance(session.files, dict) else {}
    assets = dict(session.assets or {})

    def _url(kind, filename: str):
        meta = files.get(kind)
        return generate_download_url_from_meta(meta, request=request, filename=filename)

    print_url = _url("print", "viorafilm_print.jpg")
    # UI policy: "GIF" wording is hidden; treat gif asset as video fallback.
    video_url = _url("video", "viorafilm_video.mp4")
    if not video_url:
        video_url = _url("gif", "viorafilm_video.gif")

    if print_url:
        assets["print_url"] = print_url
    if video_url:
        assets["video_url"] = video_url

    logger.info(
        "[SHARE_PAGE] token=%s status=%s file_keys=%s",
        token,
        session.status,
        sorted(files.keys()),
    )
    return render(
        request,
        "mediahub/share.html",
        {"session": session, "assets": assets, "expires_at": session.expires_at, "expired": False},
    )
