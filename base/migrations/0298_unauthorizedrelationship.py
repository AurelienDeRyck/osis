# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-02 12:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0297_auto_20180629_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnauthorizedRelationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed', models.DateTimeField(auto_now=True)),
                ('child_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unauthorized_child_type', to='base.EducationGroupType')),
                ('parent_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unauthorized_parent_type', to='base.EducationGroupType')),
            ],
        ),
    ]
