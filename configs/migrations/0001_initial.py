# Generated manually for scaffold bootstrap.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfigProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("GLOBAL", "Global"),
                            ("ORG", "Organization"),
                            ("BRANCH", "Branch"),
                            ("DEVICE", "Device"),
                        ],
                        max_length=16,
                    ),
                ),
                ("version", models.PositiveIntegerField(blank=True, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="config_profiles",
                        to="core.branch",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="config_profiles",
                        to="core.device",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="config_profiles",
                        to="core.organization",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_config_profiles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("scope", "-version", "-updated_at"),
            },
        ),
        migrations.AddConstraint(
            model_name="configprofile",
            constraint=models.UniqueConstraint(
                fields=("scope", "version"),
                condition=Q(scope="GLOBAL"),
                name="configs_profile_global_unique_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="configprofile",
            constraint=models.UniqueConstraint(
                fields=("scope", "org", "version"),
                condition=Q(scope="ORG"),
                name="configs_profile_org_unique_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="configprofile",
            constraint=models.UniqueConstraint(
                fields=("scope", "branch", "version"),
                condition=Q(scope="BRANCH"),
                name="configs_profile_branch_unique_version",
            ),
        ),
        migrations.AddConstraint(
            model_name="configprofile",
            constraint=models.UniqueConstraint(
                fields=("scope", "device", "version"),
                condition=Q(scope="DEVICE"),
                name="configs_profile_device_unique_version",
            ),
        ),
    ]
