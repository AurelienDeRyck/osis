# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-25 09:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0304_auto_20180625_1136'),
    ]

    operations = [
        migrations.RenameField(
            model_name='admissioncondition',
            old_name='text_first_bachelor_non_university',
            new_name='text_non_university_bachelors',
        ),
        migrations.RenameField(
            model_name='admissioncondition',
            old_name='text_first_bachelor_non_university_en',
            new_name='text_non_university_bachelors_en',
        ),
    ]