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

    def _url(kind):
        meta = files.get(kind)
        return generate_download_url_from_meta(meta, request=request)

    print_url = _url("print")
    frame_url = _url("frame")
    gif_url = _url("gif")
    video_url = _url("video")
    original_urls = []
    for meta in files.get("original") or []:
        u = generate_download_url_from_meta(meta, request=request)
        if u:
            original_urls.append(u)

    if print_url:
        assets["print_url"] = print_url
    if frame_url:
        assets["frame_url"] = frame_url
    if gif_url:
        assets["gif_url"] = gif_url
    if video_url:
        assets["video_url"] = video_url
    if original_urls:
        assets["original_urls"] = original_urls

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
