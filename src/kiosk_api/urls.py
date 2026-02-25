from django.urls import path

from .views import (
    AuthRefreshView,
    AuthTokenView,
    ConfigAppliedView,
    ConfigView,
    CouponCheckView,
    HeartbeatView,
    SaleCompleteView,
    ShareFinalizeView,
    ShareCompleteView,
    ShareCreateView,
    ShareInitUploadView,
    ShareUploadFileView,
    UpdateCheckView,
)

urlpatterns = [
    path("auth/token/", AuthTokenView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", AuthRefreshView.as_view(), name="token_refresh"),
    path("kiosk/heartbeat", HeartbeatView.as_view(), name="kiosk_heartbeat"),
    path("kiosk/config", ConfigView.as_view(), name="kiosk_config"),
    path("kiosk/config/applied", ConfigAppliedView.as_view(), name="kiosk_config_applied"),
    path("kiosk/updates/check", UpdateCheckView.as_view(), name="kiosk_updates_check"),
    path("kiosk/coupon/check", CouponCheckView.as_view(), name="kiosk_coupon_check"),
    path("kiosk/sales/complete", SaleCompleteView.as_view(), name="kiosk_sales_complete"),
    path("kiosk/share/create", ShareCreateView.as_view(), name="kiosk_share_create"),
    path("kiosk/share/init", ShareInitUploadView.as_view(), name="kiosk_share_init"),
    path("kiosk/share/upload", ShareUploadFileView.as_view(), name="kiosk_share_upload"),
    path("kiosk/share/finalize", ShareFinalizeView.as_view(), name="kiosk_share_finalize"),
    path("kiosk/share/complete", ShareCompleteView.as_view(), name="kiosk_share_complete"),
]
