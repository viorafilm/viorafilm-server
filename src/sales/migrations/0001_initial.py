import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("coupons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SaleTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(max_length=128)),
                ("layout_id", models.CharField(max_length=32)),
                ("prints", models.IntegerField(default=2)),
                ("currency", models.CharField(default="KRW", max_length=8)),
                ("price_total", models.IntegerField()),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("CASH", "CASH"),
                            ("CARD", "CARD"),
                            ("COUPON", "COUPON"),
                            ("COUPON_CASH", "COUPON_CASH"),
                            ("TEST", "TEST"),
                        ],
                        max_length=16,
                    ),
                ),
                ("amount_cash", models.IntegerField(default=0)),
                ("amount_coupon", models.IntegerField(default=0)),
                ("meta", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "branch",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sales", to="core.branch"),
                ),
                (
                    "coupon",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales", to="coupons.coupon"),
                ),
                (
                    "device",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sales", to="core.device"),
                ),
                (
                    "org",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sales", to="core.organization"),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="saletransaction",
            constraint=models.UniqueConstraint(fields=("device", "session_id"), name="uniq_sale_device_session"),
        ),
        migrations.AddIndex(
            model_name="saletransaction",
            index=models.Index(fields=["created_at"], name="sales_sale_created_32e9ec_idx"),
        ),
        migrations.AddIndex(
            model_name="saletransaction",
            index=models.Index(fields=["org", "branch", "device"], name="sales_sale_org_id_2f56fb_idx"),
        ),
    ]

