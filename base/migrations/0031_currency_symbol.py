# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-17 19:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0030_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='symbol',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
