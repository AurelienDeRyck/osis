# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-27 08:46
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


def _round_credits_in_education_group_year():
    return "update base_educationgroupyear set credits=ceil(credits), min_credits=ceil(min_credits), max_credits=ceil(max_credits);"


def _round_credits_in_group_elemement_year():
    return "update base_groupelementyear set relative_credits=ceil(relative_credits), min_credits=ceil(min_credits), max_credits=ceil(max_credits);"


def _round_credits_in_learning_unit_year():
    return "update base_learningunityear set credits=ceil(credits);"


def _round_credits_in_external_learning_unit_year():
    return "update base_externallearningunityear set external_credits=ceil(external_credits);"


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0320_remove_groupelementyear_sessions_derogation'),
    ]

    operations = [
        migrations.RunSQL(_round_credits_in_education_group_year()),
        migrations.RunSQL(_round_credits_in_group_elemement_year()),
        migrations.RunSQL(_round_credits_in_learning_unit_year()),
        migrations.RunSQL(_round_credits_in_external_learning_unit_year()),
    ]

