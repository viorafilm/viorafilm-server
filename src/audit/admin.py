from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "target_type", "target_id", "actor_user", "actor_device")
    list_filter = ("action", "target_type")
    search_fields = ("target_id", "action")

