from django.contrib import admin

from audit.service import log_event

from .models import ConfigProfile


@admin.register(ConfigProfile)
class ConfigProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "scope", "org", "branch", "device", "version", "updated_by", "updated_at")
    list_filter = ("scope", "org", "branch", "device")
    search_fields = ("org__code", "branch__code", "device__device_code")
    readonly_fields = ("updated_at",)
    autocomplete_fields = ("org", "branch", "device", "updated_by")

    @staticmethod
    def _snapshot(obj: ConfigProfile) -> dict:
        payload = obj.payload if isinstance(obj.payload, dict) else {}
        return {
            "id": obj.pk,
            "scope": obj.scope,
            "org_id": obj.org_id,
            "branch_id": obj.branch_id,
            "device_id": obj.device_id,
            "version": obj.version,
            "payload": payload,
            "updated_by_id": obj.updated_by_id,
        }

    @staticmethod
    def _request_ip(request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if isinstance(forwarded, str) and forwarded.strip():
            return forwarded.split(",")[0].strip()
        remote = request.META.get("REMOTE_ADDR")
        if isinstance(remote, str) and remote.strip():
            return remote.strip()
        return None

    def save_model(self, request, obj, form, change):
        before = None
        if change and obj.pk:
            old = ConfigProfile.objects.filter(pk=obj.pk).first()
            if old is not None:
                before = self._snapshot(old)

        actor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        if actor is not None:
            obj.updated_by = actor

        super().save_model(request, obj, form, change)

        action = "config.update" if change else "config.create"
        log_event(
            actor_user=actor,
            action=action,
            target_type="ConfigProfile",
            target_id=str(obj.pk),
            before=before,
            after=self._snapshot(obj),
            meta={
                "scope": obj.scope,
                "admin_path": request.path,
                "method": request.method,
            },
            ip=self._request_ip(request),
        )
