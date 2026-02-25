import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("code", models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("code", models.CharField(max_length=64)),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="branches", to="core.organization"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Device",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("device_code", models.CharField(max_length=64, unique=True)),
                ("display_name", models.CharField(blank=True, default="", max_length=200)),
                ("is_active", models.BooleanField(default=True)),
                ("token_hash", models.CharField(blank=True, default="", max_length=64)),
                ("token_hint", models.CharField(blank=True, default="", max_length=16)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("last_app_version", models.CharField(blank=True, max_length=32, null=True)),
                ("last_config_version_applied", models.CharField(blank=True, max_length=64, null=True)),
                ("last_config_applied_at", models.DateTimeField(blank=True, null=True)),
                ("last_health_json", models.JSONField(blank=True, default=dict)),
                (
                    "branch",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="core.branch"),
                ),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="core.organization"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="branch",
            constraint=models.UniqueConstraint(fields=("org", "code"), name="uniq_branch_code_per_org"),
        ),
    ]
