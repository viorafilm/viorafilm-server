from django.contrib import admin

from .models import Alert, NotificationChannel


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("device", "alert_type", "severity", "created_at", "resolved_at")
    list_filter = ("alert_type", "severity")
    search_fields = ("device__device_code",)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("type", "org", "enabled", "created_at")
    list_filter = ("type", "enabled")

