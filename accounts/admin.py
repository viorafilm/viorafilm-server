from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Branch, Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "updated_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "code", "is_active", "updated_at")
    search_fields = ("name", "code", "organization__name")
    list_filter = ("organization", "is_active")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "role",
        "organization",
        "branch",
        "is_active",
        "last_login",
    )
    list_filter = ("role", "is_active", "is_staff", "organization", "branch")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Kiosk Access", {"fields": ("role", "organization", "branch")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Kiosk Access", {"fields": ("role", "organization", "branch")}),
    )
