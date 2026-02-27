from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    coupons_view,
    devices_view,
    devices_live_view,
    index_view,
    index_live_view,
    login_view,
    photos_view,
    sales_view,
)

urlpatterns = [
    path("login", login_view, name="dashboard_login"),
    path("logout", LogoutView.as_view(next_page="/dashboard/login"), name="dashboard_logout"),
    path("", index_view, name="dashboard_index"),
    path("live/index", index_live_view, name="dashboard_index_live"),
    path("devices", devices_view, name="dashboard_devices"),
    path("live/devices", devices_live_view, name="dashboard_devices_live"),
    path("sales", sales_view, name="dashboard_sales"),
    path("coupons", coupons_view, name="dashboard_coupons"),
    path("photos", photos_view, name="dashboard_photos"),
]
