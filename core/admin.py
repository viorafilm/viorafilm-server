from django.contrib import admin, messages

from .models import Branch, Device, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "org")
    search_fields = ("code", "name", "org__code", "org__name")
    list_filter = ("org",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_code",
        "branch",
        "is_active",
        "last_seen_at",
        "last_app_version",
        "token_hint",
    )
    list_filter = ("is_active", "org", "branch")
    search_fields = ("device_code", "display_name", "branch__code", "org__code")
    readonly_fields = ("token_hash", "token_hint", "created_at", "updated_at")
    actions = ("rotate_device_token",)

    @admin.action(description="Rotate device token")
    def rotate_device_token(self, request, queryset):
        tokens: list[str] = []
        for device in queryset:
            raw = device.rotate_token()
            tokens.append(f"{device.device_code}={raw}")

        if not tokens:
            self.message_user(request, "No device selected.", level=messages.WARNING)
            return

        if len(tokens) <= 3:
            token_text = " | ".join(tokens)
        else:
            preview = " | ".join(tokens[:3])
            token_text = f"{preview} | ... (+{len(tokens) - 3} more)"
        self.message_user(
            request,
            f"Device token rotated (show-once): {token_text}",
            level=messages.SUCCESS,
        )
