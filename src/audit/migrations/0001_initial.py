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
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("action", models.CharField(max_length=128)),
                ("target_type", models.CharField(max_length=128)),
                ("target_id", models.CharField(max_length=128)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                (
                    "actor_device",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.device"),
                ),
                (
                    "actor_user",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.user"),
                ),
            ],
        ),
    ]

