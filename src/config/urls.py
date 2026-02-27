from datetime import timedelta

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.urls import include, path
from django.utils import timezone
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    db_ok = False
    redis_ok = False
    db_error = ""
    redis_error = ""
    open_alerts = 0
    active_devices = 0
    online_devices = 0

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    try:
        from redis import Redis

        redis_url = str(getattr(settings, "CELERY_BROKER_URL", "") or "").strip()
        if redis_url:
            redis_client = Redis.from_url(redis_url, socket_connect_timeout=1.0, socket_timeout=1.0)
            redis_ok = bool(redis_client.ping())
        else:
            redis_error = "CELERY_BROKER_URL missing"
    except Exception as exc:
        redis_error = str(exc)

    try:
        from alerts.models import Alert
        from core.models import Device

        threshold = int(getattr(settings, "OFFLINE_THRESHOLD_SECONDS", 120))
        cutoff = timezone.now() - timedelta(seconds=max(30, threshold))
        open_alerts = int(Alert.objects.filter(resolved_at__isnull=True).count())
        active_devices = int(Device.objects.filter(is_active=True).count())
        online_devices = int(Device.objects.filter(is_active=True, last_seen_at__gte=cutoff).count())
    except Exception:
        pass

    ok = bool(db_ok and redis_ok)
    payload = {
        "ok": ok,
        "service": "viorafilm-api",
        "time": timezone.now().isoformat(),
        "checks": {
            "db": {"ok": db_ok, "error": db_error or None},
            "redis": {"ok": redis_ok, "error": redis_error or None},
        },
        "stats": {
            "active_devices": active_devices,
            "online_devices": online_devices,
            "open_alerts": open_alerts,
        },
    }
    return Response(payload, status=200 if ok else 503)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]), name="swagger-ui"),
    path("api/", include("kiosk_api.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", include("mediahub.urls")),
]

# Serve static/media directly from Django.
# This keeps admin/docs CSS working even when Nginx static alias is not configured yet.
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
