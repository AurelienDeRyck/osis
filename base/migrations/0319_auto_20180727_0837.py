# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-27 06:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0318_remove_educationgroupyear_fee_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupelementyear',
            name='link_type',
            field=models.CharField(blank=True, choices=[('REFERENCE', 'REFERENCE')], max_length=25, null=True,
                                   verbose_name='Link type'),
        ),
        migrations.AddField(
            model_name='groupelementyear',
            name='quadrimester_derogation',
            field=models.CharField(blank=True,
                                   choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q1 or Q2', 'Q1 or Q2'), ('Q3', 'Q3')],
                                   max_length=10, null=True, verbose_name='Quadrimester derogation'),
        ),
    ]
