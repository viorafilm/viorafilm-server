from django.contrib import admin

from .models import Alert, NotificationChannel


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "alert_type",
        "severity",
        "created_at",
        "resolved_at",
        "last_notified_at",
    )
    list_filter = ("alert_type", "severity", "resolved_at", "device__org")
    search_fields = ("device__device_code", "message")
    readonly_fields = ("created_at", "last_notified_at")


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("type", "org", "enabled", "updated_at")
    list_filter = ("type", "enabled", "org")
    search_fields = ("org__code", "org__name")

