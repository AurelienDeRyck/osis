# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-18 09:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0033_postalcode'),
    ]

    operations = [
        migrations.RenameField(
            model_name='country',
            old_name='acronym',
            new_name='iso_code',
        ),
    ]
