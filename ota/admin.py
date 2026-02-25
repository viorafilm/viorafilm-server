from django.contrib import admin, messages
from django.db import transaction

from audit.service import log_event

from .models import AppRelease


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = (
        "platform",
        "version",
        "is_active",
        "min_supported_version",
        "force_below_min",
        "sha256",
        "created_at",
    )
    list_filter = ("platform", "is_active", "force_below_min")
    search_fields = ("version", "sha256", "notes")
    readonly_fields = ("created_at",)
    actions = ("set_as_active_release",)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @staticmethod
    def _request_ip(request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if isinstance(forwarded, str) and forwarded.strip():
            return forwarded.split(",")[0].strip()
        remote = request.META.get("REMOTE_ADDR")
        if isinstance(remote, str) and remote.strip():
            return remote.strip()
        return None

    @admin.action(description="Set as active release")
    def set_as_active_release(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Select exactly one release.", level=messages.WARNING)
            return

        target = queryset.first()
        if target is None:
            self.message_user(request, "No release selected.", level=messages.WARNING)
            return

        with transaction.atomic():
            previous_active = (
                AppRelease.objects.select_for_update()
                .filter(platform=target.platform, is_active=True)
                .exclude(pk=target.pk)
                .first()
            )
            AppRelease.objects.filter(platform=target.platform).exclude(pk=target.pk).update(is_active=False)
            if not target.is_active:
                target.is_active = True
                target.save(update_fields=["is_active"])

        log_event(
            actor_user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            action="release.activate",
            target_type="AppRelease",
            target_id=str(target.pk),
            before={
                "platform": target.platform,
                "previous_active": previous_active.version if previous_active else None,
            },
            after={
                "platform": target.platform,
                "active_version": target.version,
            },
            meta={
                "platform": target.platform,
                "selected_version": target.version,
                "admin_path": request.path,
                "method": request.method,
            },
            ip=self._request_ip(request),
        )

        self.message_user(
            request,
            f"Active release set: {target.platform} {target.version}",
            level=messages.SUCCESS,
        )
