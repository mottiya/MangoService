# Generated by Django 4.2.1 on 2023-05-24 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mangoapi', '0002_remove_call_from_remove_call_to_call_from_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='send_flag',
            field=models.BooleanField(default=False),
        ),
    ]
