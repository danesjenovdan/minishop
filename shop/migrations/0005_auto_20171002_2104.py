# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-02 21:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_auto_20171002_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payer_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]