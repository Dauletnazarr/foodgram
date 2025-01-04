# Generated by Django 4.2.17 on 2024-12-26 13:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_ownuser_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownuser',
            name='avatar',
            field=models.ImageField(default=None, null=True, upload_to='users/avatars/'),
        ),
        migrations.AddField(
            model_name='ownuser',
            name='is_subscribed',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscribed_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'subscribed_to')},
            },
        ),
    ]
