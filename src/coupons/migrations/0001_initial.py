import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import coupons.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CouponBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, default="", max_length=200)),
                ("amount", models.IntegerField(default=0)),
                ("count", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "branch",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.branch"),
                ),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.user"),
                ),
                (
                    "org",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.organization"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Coupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=6, unique=True)),
                ("amount", models.IntegerField(default=0)),
                ("currency", models.CharField(default="KRW", max_length=8)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(default=coupons.models._default_expires_at)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("used_session_id", models.CharField(blank=True, max_length=128, null=True)),
                ("meta", models.JSONField(blank=True, default=dict)),
                (
                    "batch",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coupons", to="coupons.couponbatch"),
                ),
                (
                    "used_by_device",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.device"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="coupon",
            index=models.Index(fields=["expires_at"], name="coupons_cou_expires_a_27b04a_idx"),
        ),
        migrations.AddIndex(
            model_name="coupon",
            index=models.Index(fields=["used_at"], name="coupons_cou_used_at_4e8a32_idx"),
        ),
    ]

