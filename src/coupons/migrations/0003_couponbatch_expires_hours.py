from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coupons", "0002_rename_coupons_cou_expires_a_27b04a_idx_coupons_cou_expires_292eae_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="couponbatch",
            name="expires_hours",
            field=models.PositiveIntegerField(default=24),
        ),
    ]

