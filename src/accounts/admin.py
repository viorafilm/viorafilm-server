from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Photoharu", {"fields": ("role", "organization", "branch")}),
    )
    list_display = ("username", "role", "organization", "branch", "is_active", "last_login")
    list_filter = ("role", "is_active")

