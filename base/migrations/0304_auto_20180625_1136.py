# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-25 09:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0303_auto_20180625_1135'),
    ]

    operations = [
        migrations.RenameField(
            model_name='admissioncondition',
            old_name='text_bachelor_university',
            new_name='text_university_bachelors',
        ),
        migrations.RenameField(
            model_name='admissioncondition',
            old_name='text_bachelor_university_en',
            new_name='text_university_bachelors_en',
        ),
    ]