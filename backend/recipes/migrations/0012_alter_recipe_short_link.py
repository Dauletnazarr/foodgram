# Generated by Django 4.2.17 on 2025-01-10 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0011_subscription_prevent_self_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='short_link',
            field=models.CharField(default=1, max_length=128, verbose_name='Короткая ссылка'),
            preserve_default=False,
        ),
    ]
