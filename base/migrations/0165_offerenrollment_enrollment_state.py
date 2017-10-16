# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-16 10:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0164_educationgroupyear_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='offerenrollment',
            name='enrollment_state',
            field=models.CharField(blank=True, choices=[('SUBSCRIBED', 'SUBSCRIBED'), ('PROVISORY', 'PROVISORY')], max_length=15, null=True),
        ),
    ]
