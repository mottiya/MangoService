# Generated by Django 4.2.1 on 2023-06-01 11:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mangoapi', '0007_tgnotifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='advert',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2023, 6, 1, 11, 42, 6, 900354)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='call',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2023, 6, 1, 11, 43, 35, 819723, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
