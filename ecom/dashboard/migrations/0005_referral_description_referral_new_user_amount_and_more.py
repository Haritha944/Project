# Generated by Django 4.2.7 on 2024-02-05 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_referral_created_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='referral',
            name='new_user_amount',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='referral',
            name='referred_user_amount',
            field=models.FloatField(default=0),
        ),
    ]
