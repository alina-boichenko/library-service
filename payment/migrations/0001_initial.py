# Generated by Django 4.2.2 on 2023-06-26 10:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("borrowing", "0003_alter_borrowing_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("PENDING", "pending"), ("PAID", "paid")],
                        default="pending",
                        max_length=7,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("PAYMENT", "payment"), ("FINE", "fine")], max_length=7
                    ),
                ),
                ("session_url", models.TextField()),
                ("session_id", models.TextField()),
                ("money_to_pay", models.DecimalField(decimal_places=2, max_digits=7)),
                (
                    "borrowing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="borrowing.borrowing",
                    ),
                ),
            ],
        ),
    ]
