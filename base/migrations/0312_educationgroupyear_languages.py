# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-19 17:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0017_language_changed'),
        ('base', '0311_auto_20180719_1551'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationgroupyear',
            name='languages',
            field=models.ManyToManyField(related_name='education_group_years', through='base.EducationGroupLanguage', to='reference.Language'),
        ),
    ]