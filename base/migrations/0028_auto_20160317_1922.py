# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-17 18:22
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0027_languages'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Countries',
            new_name='Country',
        ),
    ]
