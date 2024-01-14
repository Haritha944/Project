# Generated by Django 4.2.7 on 2024-01-13 17:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_productimage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cart', '0003_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productvariant')),
            ],
        ),
    ]