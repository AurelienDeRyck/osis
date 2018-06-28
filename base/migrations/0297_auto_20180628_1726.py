# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-06-28 15:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0296_admissioncondition_admissionconditionline'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionconditionline',
            name='external_id',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='admissioncondition',
            name='text_standard',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissioncondition',
            name='text_standard_en',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='access',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='access_en',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='conditions',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='conditions_en',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='diploma',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='diploma_en',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='remarks',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='admissionconditionline',
            name='remarks_en',
            field=models.TextField(default=''),
        ),
    ]
