# Generated manually for scaffold bootstrap.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AppRelease",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("platform", models.CharField(choices=[("win", "Windows")], default="win", max_length=16)),
                ("version", models.CharField(max_length=64)),
                ("is_active", models.BooleanField(default=False)),
                ("min_supported_version", models.CharField(default="0.0.0", max_length=64)),
                ("force_below_min", models.BooleanField(default=True)),
                ("artifact", models.FileField(upload_to="releases/")),
                ("sha256", models.CharField(max_length=64)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_releases",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("platform", "-created_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(
                fields=("platform",),
                condition=Q(is_active=True),
                name="ota_one_active_release_per_platform",
            ),
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(
                fields=("platform", "version"),
                name="ota_unique_platform_version",
            ),
        ),
    ]
