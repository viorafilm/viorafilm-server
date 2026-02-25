from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "target_type", "target_id", "actor_user", "actor_device", "ip")
    list_filter = ("action", "target_type", "actor_user", "actor_device")
    search_fields = ("action", "target_type", "target_id", "actor_user__username", "actor_device__device_code")
    readonly_fields = ("created_at",)
