from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Super Admin"
    ORG_ADMIN = "ORG_ADMIN", "Org Admin"
    BRANCH_ADMIN = "BRANCH_ADMIN", "Branch Admin"
    VIEWER = "VIEWER", "Viewer"


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.VIEWER)
    organization = models.ForeignKey(
        "core.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    branch = models.ForeignKey(
        "core.Branch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

