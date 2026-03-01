from django.contrib import admin, messages
from django.utils import timezone

from .models import Branch, Device, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "org")
    list_filter = ("org",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_code",
        "display_name",
        "branch",
        "org",
        "is_active",
        "allow_celebrity_mode",
        "allow_ai_mode",
        "is_locked",
        "locked_at",
        "last_seen_at",
        "last_app_version",
        "token_hint",
    )
    list_filter = ("org", "branch", "is_active", "allow_celebrity_mode", "allow_ai_mode", "is_locked")
    search_fields = ("device_code", "display_name")
    actions = ["rotate_device_token", "lock_selected_devices", "unlock_selected_devices"]

    @admin.action(description="Rotate device token (shows new token once)")
    def rotate_device_token(self, request, queryset):
        for device in queryset:
            raw = device.rotate_token()
            self.message_user(
                request,
                f"[{device.device_code}] NEW TOKEN (save now): {raw}",
                level=messages.WARNING,
            )

    @admin.action(description="Lock selected devices")
    def lock_selected_devices(self, request, queryset):
        count = 0
        for device in queryset:
            if device.is_locked:
                continue
            device.is_locked = True
            device.lock_reason = "locked by admin"
            device.locked_at = timezone.now()
            device.save(update_fields=["is_locked", "lock_reason", "locked_at", "updated_at"])
            count += 1
        self.message_user(request, f"Locked devices: {count}", level=messages.INFO)

    @admin.action(description="Unlock selected devices")
    def unlock_selected_devices(self, request, queryset):
        count = 0
        for device in queryset:
            if not device.is_locked:
                continue
            device.is_locked = False
            device.lock_reason = ""
            device.locked_at = None
            device.save(update_fields=["is_locked", "lock_reason", "locked_at", "updated_at"])
            count += 1
        self.message_user(request, f"Unlocked devices: {count}", level=messages.INFO)
