from django.contrib import admin

from .models import UploadAsset


@admin.register(UploadAsset)
class UploadAssetAdmin(admin.ModelAdmin):
    list_display = ("created_at", "device", "share", "kind", "storage_backend", "object_key", "file", "size_bytes")
    list_filter = ("kind", "storage_backend", "created_at")
    search_fields = ("device__device_code", "share__token", "file", "object_key", "original_filename")
