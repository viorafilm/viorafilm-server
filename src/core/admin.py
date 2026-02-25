from django.contrib import admin, messages

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
        "last_seen_at",
        "last_app_version",
        "token_hint",
    )
    list_filter = ("org", "branch", "is_active")
    search_fields = ("device_code", "display_name")
    actions = ["rotate_device_token"]

    @admin.action(description="Rotate device token (shows new token once)")
    def rotate_device_token(self, request, queryset):
        for device in queryset:
            raw = device.rotate_token()
            self.message_user(
                request,
                f"[{device.device_code}] NEW TOKEN (save now): {raw}",
                level=messages.WARNING,
            )

