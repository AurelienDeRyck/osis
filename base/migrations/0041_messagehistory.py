# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-02 22:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_scoresencoding'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('origin', models.EmailField(max_length=254)),
                ('created', models.DateTimeField(editable=False)),
                ('sent', models.DateTimeField(null=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person')),
            ],
        ),
    ]
