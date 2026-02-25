from django.contrib import admin

from .models import ShareSession


@admin.register(ShareSession)
class ShareSessionAdmin(admin.ModelAdmin):
    list_display = ("token", "device", "created_at", "expires_at", "view_count", "download_count")
    search_fields = ("token", "device__device_code")
    list_filter = ("created_at", "expires_at")
    readonly_fields = ("created_at",)

