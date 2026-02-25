import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("mediahub", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("PRINT", "PRINT"),
                            ("FRAME", "FRAME"),
                            ("GIF", "GIF"),
                            ("VIDEO", "VIDEO"),
                            ("ORIGINAL", "ORIGINAL"),
                        ],
                        max_length=16,
                    ),
                ),
                ("file", models.FileField(upload_to="uploads/%Y/%m/%d/")),
                ("content_type", models.CharField(blank=True, default="", max_length=128)),
                ("size_bytes", models.BigIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.device")),
                (
                    "share",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="uploads",
                        to="mediahub.sharesession",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="uploadasset",
            index=models.Index(fields=["kind", "created_at"], name="storagehub_u_kind_120607_idx"),
        ),
    ]
