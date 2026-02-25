import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppRelease",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("platform", models.CharField(choices=[("win", "Windows")], default="win", max_length=8)),
                ("version", models.CharField(max_length=32)),
                ("is_active", models.BooleanField(default=False)),
                ("min_supported_version", models.CharField(default="0.0.0", max_length=32)),
                ("force_below_min", models.BooleanField(default=True)),
                ("artifact", models.FileField(upload_to="releases/")),
                ("sha256", models.CharField(blank=True, default="", max_length=64)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="apprelease",
            index=models.Index(fields=["platform", "is_active"], name="ota_apprel_platfor_c44032_idx"),
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(
                fields=("platform",),
                condition=Q(is_active=True),
                name="ota_one_active_per_platform",
            ),
        ),
        migrations.AddConstraint(
            model_name="apprelease",
            constraint=models.UniqueConstraint(fields=("platform", "version"), name="ota_unique_platform_version"),
        ),
    ]
