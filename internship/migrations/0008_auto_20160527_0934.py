# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-27 07:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('internship', '0007_auto_20160517_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='changed',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='external_id',
        ),
    ]
