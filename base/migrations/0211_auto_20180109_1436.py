# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-09 13:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0210_auto_20180105_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningunityear',
            name='attribution_procedure',
            field=models.CharField(blank=True, choices=[('INTERNAL_TEAM', 'INTERNAL_TEAM'), ('EXTERNAL', 'EXTERNAL')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='learningunityear',
            name='quadrimester',
            field=models.CharField(blank=True, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q1&2', 'Q1&2'), ('Q1|2', 'Q1|2'), ('Q3', 'Q3')], max_length=4, null=True),
        ),
    ]
