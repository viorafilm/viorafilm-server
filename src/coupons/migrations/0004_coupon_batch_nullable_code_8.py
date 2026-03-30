from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coupons", "0003_couponbatch_expires_hours"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coupon",
            name="batch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name="coupons",
                to="coupons.couponbatch",
            ),
        ),
        migrations.AlterField(
            model_name="coupon",
            name="code",
            field=models.CharField(max_length=8, unique=True),
        ),
    ]
