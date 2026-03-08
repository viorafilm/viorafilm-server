from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_device_install_binding"),
        ("sales", "0002_rename_sales_sale_created_32e9ec_idx_sales_salet_created_7a0b54_idx_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BranchMonthlyBilling",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("billing_month", models.DateField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PAID", "Paid")], default="PENDING", max_length=16)),
                ("note", models.CharField(blank=True, default="", max_length=255)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monthly_billings", to="core.branch")),
                ("org", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monthly_billings", to="core.organization")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_monthly_billings", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["billing_month", "status"], name="sales_branc_billing_4d922a_idx"),
                    models.Index(fields=["org", "branch"], name="sales_branc_org_id_0d57fe_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="branchmonthlybilling",
            constraint=models.UniqueConstraint(fields=("branch", "billing_month"), name="uniq_branch_monthly_billing"),
        ),
    ]
