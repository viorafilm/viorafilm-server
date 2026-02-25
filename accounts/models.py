from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Branch(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="branches",
    )
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_branch_code_per_org",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name} / {self.name}"


class User(AbstractUser):
    ROLE_SUPERADMIN = "SUPERADMIN"
    ROLE_ORG_ADMIN = "ORG_ADMIN"
    ROLE_BRANCH_ADMIN = "BRANCH_ADMIN"
    ROLE_VIEWER = "VIEWER"

    ROLE_CHOICES = (
        (ROLE_SUPERADMIN, "Super Admin"),
        (ROLE_ORG_ADMIN, "Organization Admin"),
        (ROLE_BRANCH_ADMIN, "Branch Admin"),
        (ROLE_VIEWER, "Viewer"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    class Meta:
        ordering = ("username",)

    def __str__(self) -> str:
        return self.username
