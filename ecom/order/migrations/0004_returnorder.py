# Generated by Django 4.2.7 on 2024-01-11 17:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_orderitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('return_reason', models.CharField(max_length=100, null=True)),
                ('return_comment', models.TextField(max_length=500, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.order')),
                ('order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.orderitem')),
            ],
        ),
    ]