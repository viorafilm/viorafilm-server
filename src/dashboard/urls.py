from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    coupons_view,
    devices_view,
    index_view,
    login_view,
    photos_view,
    sales_view,
)

urlpatterns = [
    path("login", login_view, name="dashboard_login"),
    path("logout", LogoutView.as_view(next_page="/dashboard/login"), name="dashboard_logout"),
    path("", index_view, name="dashboard_index"),
    path("devices", devices_view, name="dashboard_devices"),
    path("sales", sales_view, name="dashboard_sales"),
    path("coupons", coupons_view, name="dashboard_coupons"),
    path("photos", photos_view, name="dashboard_photos"),
]

