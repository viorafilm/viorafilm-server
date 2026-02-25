from django.db import migrations, models
import django.db.models.deletion
import mediahub.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShareSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(db_index=True, max_length=128, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "expires_at",
                    models.DateTimeField(default=mediahub.models.default_share_expiry),
                ),
                ("assets", models.JSONField(blank=True, default=dict)),
                ("view_count", models.PositiveIntegerField(default=0)),
                ("download_count", models.PositiveIntegerField(default=0)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="share_sessions",
                        to="core.device",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
