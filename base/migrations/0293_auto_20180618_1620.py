# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-18 14:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0292_remove_admissioncondition_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='admissionconditionsubline',
            old_name='condition',
            new_name='conditions',
        ),
        migrations.RenameField(
            model_name='admissionconditionsubline',
            old_name='diplome',
            new_name='diploma',
        ),
        migrations.RenameField(
            model_name='admissionconditionsubline',
            old_name='remarques',
            new_name='remarks',
        ),
    ]