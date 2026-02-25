from django.contrib import admin

from .models import DeviceHeartbeat


@admin.register(DeviceHeartbeat)
class DeviceHeartbeatAdmin(admin.ModelAdmin):
    list_display = ("device", "created_at", "internet_ok", "camera_ok", "printer_ok")
    list_filter = ("internet_ok", "camera_ok", "printer_ok", "device__org", "device__branch")
    search_fields = ("device__device_code", "device__display_name")
    readonly_fields = ("created_at",)
