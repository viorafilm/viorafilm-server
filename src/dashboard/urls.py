from django.urls import path

from .views import (
    billing_view,
    coupons_view,
    coupons_export_view,
    currency_unit_view,
    dashboard_timezone_view,
    devices_view,
    devices_live_view,
    index_view,
    index_live_view,
    login_view,
    ops_view,
    logout_view,
    photos_view,
    sales_view,
    sales_export_view,
)

urlpatterns = [
    path("login", login_view, name="dashboard_login"),
    path("logout", logout_view, name="dashboard_logout"),
    path("currency-unit", currency_unit_view, name="dashboard_currency_unit"),
    path("timezone", dashboard_timezone_view, name="dashboard_timezone"),
    path("", index_view, name="dashboard_index"),
    path("live/index", index_live_view, name="dashboard_index_live"),
    path("devices", devices_view, name="dashboard_devices"),
    path("live/devices", devices_live_view, name="dashboard_devices_live"),
    path("ops", ops_view, name="dashboard_ops"),
    path("billing", billing_view, name="dashboard_billing"),
    path("sales", sales_view, name="dashboard_sales"),
    path("sales/export", sales_export_view, name="dashboard_sales_export"),
    path("coupons", coupons_view, name="dashboard_coupons"),
    path("coupons/export", coupons_export_view, name="dashboard_coupons_export"),
    path("photos", photos_view, name="dashboard_photos"),
]
