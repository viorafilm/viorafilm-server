from django.urls import include, path

from .views import (
    HeartbeatAPIView,
    KioskConfigAPIView,
    KioskConfigAppliedAPIView,
    KioskUpdatesCheckAPIView,
)

urlpatterns = [
    path("heartbeat", HeartbeatAPIView.as_view(), name="kiosk-heartbeat"),
    path("heartbeat/", HeartbeatAPIView.as_view(), name="kiosk-heartbeat-slash"),
    path("config", KioskConfigAPIView.as_view(), name="kiosk-config"),
    path("config/", KioskConfigAPIView.as_view(), name="kiosk-config-slash"),
    path("config/applied", KioskConfigAppliedAPIView.as_view(), name="kiosk-config-applied"),
    path("config/applied/", KioskConfigAppliedAPIView.as_view(), name="kiosk-config-applied-slash"),
    path("updates/check", KioskUpdatesCheckAPIView.as_view(), name="kiosk-updates-check"),
    path("updates/check/", KioskUpdatesCheckAPIView.as_view(), name="kiosk-updates-check-slash"),
    path("share/", include("mediahub.kiosk_urls")),
]
