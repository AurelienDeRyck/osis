# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-26 14:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0171_auto_20171017_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningunityear',
            name='quadrimester',
            field=models.CharField(blank=True, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q1&2', 'Q1&2'), ('Q1|2', 'Q1|2')], max_length=4, null=True),
        ),
    ]
