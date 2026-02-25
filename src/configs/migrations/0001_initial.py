import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfigProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(choices=[("GLOBAL", "GLOBAL"), ("ORG", "ORG"), ("BRANCH", "BRANCH"), ("DEVICE", "DEVICE")], max_length=16)),
                ("version", models.PositiveIntegerField(default=0)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "branch",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="core.branch"),
                ),
                (
                    "device",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="core.device"),
                ),
                (
                    "org",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="core.organization"),
                ),
                (
                    "updated_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="configprofile",
            index=models.Index(fields=["scope", "version"], name="configs_con_scope_088f75_idx"),
        ),
    ]

