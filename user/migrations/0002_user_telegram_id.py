# Generated by Django 4.2.2 on 2023-06-14 14:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="telegram_id",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="user ID in telegram"
            ),
        ),
    ]
