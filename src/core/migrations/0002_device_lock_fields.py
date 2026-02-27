from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="is_locked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="device",
            name="lock_reason",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="device",
            name="locked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
