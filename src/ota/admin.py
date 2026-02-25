import hashlib

from django.contrib import admin, messages
from django.db import transaction

from audit.service import log_event

from .models import AppRelease


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ("platform", "version", "is_active", "min_supported_version", "force_below_min", "created_at")
    list_filter = ("platform", "is_active")
    search_fields = ("version",)
    actions = ["set_active_release"]

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user if not obj.created_by else obj.created_by
        super().save_model(request, obj, form, change)
        if obj.artifact and not obj.sha256:
            digest = hashlib.sha256()
            with obj.artifact.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(chunk)
            obj.sha256 = digest.hexdigest()
            obj.save(update_fields=["sha256"])
            self.message_user(request, f"sha256 computed: {obj.sha256}", level=messages.INFO)

    @admin.action(description="Set selected release as ACTIVE (supports rollback)")
    def set_active_release(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Select exactly 1 release.", level=messages.ERROR)
            return
        new_active = queryset.first()
        with transaction.atomic():
            old_active = AppRelease.objects.filter(platform=new_active.platform, is_active=True).first()
            AppRelease.objects.filter(platform=new_active.platform, is_active=True).update(is_active=False)
            new_active.is_active = True
            new_active.save(update_fields=["is_active"])

        log_event(
            actor_user=request.user,
            actor_device=None,
            action="release.activate",
            target_type="AppRelease",
            target_id=str(new_active.pk),
            before={
                "old_active": str(old_active.pk) if old_active else None,
                "old_version": old_active.version if old_active else None,
            },
            after={
                "new_active": str(new_active.pk),
                "new_version": new_active.version,
            },
            meta={"platform": new_active.platform},
            ip=request.META.get("REMOTE_ADDR"),
        )
        self.message_user(
            request,
            f"ACTIVE set to {new_active.platform}:{new_active.version}",
            level=messages.SUCCESS,
        )

