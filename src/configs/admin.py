from django.contrib import admin

from audit.service import log_event

from .models import ConfigProfile


@admin.register(ConfigProfile)
class ConfigProfileAdmin(admin.ModelAdmin):
    list_display = ("scope", "org", "branch", "device", "version", "updated_by", "updated_at")
    list_filter = ("scope", "org")
    search_fields = ("org__code", "branch__code", "device__device_code")

    def save_model(self, request, obj, form, change):
        before = None
        if change:
            old = ConfigProfile.objects.get(pk=obj.pk)
            before = {"payload": old.payload, "version": old.version, "scope": old.scope}
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        after = {"payload": obj.payload, "version": obj.version, "scope": obj.scope}
        log_event(
            actor_user=request.user,
            actor_device=None,
            action="config.update",
            target_type="ConfigProfile",
            target_id=str(obj.pk),
            before=before,
            after=after,
            meta={"scope": obj.scope},
            ip=request.META.get("REMOTE_ADDR"),
        )

