# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-04 03:40
from __future__ import unicode_literals
from django.conf import settings

from django.db import migrations, models, connection
from django.utils import translation
from reference.models import grade_type as mdl_grade_type
from reference.models.enums import institutional_grade_type as instit_grade_type_enum
from django.utils.translation import ugettext_lazy as _


def get_key_from_value_institu_great_type_enum(instit_grade_type_name):
    if not instit_grade_type_name:
        return None
    for key, value in instit_grade_type_enum.INSTITUTIONAL_GRADE_CHOICES:
        lang_dict = {lang[0]: [] for lang in settings.LANGUAGES}
        for lang in lang_dict:
            translation.activate(lang)
            if _(value) == instit_grade_type_name or value == instit_grade_type_name or key == instit_grade_type_name:
                translation.deactivate()
                return key
            translation.deactivate()
    return None


def move_fk_to_enum(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("select gt.id, igt.name from reference_gradetype gt, reference_institutionalgradetype igt where gt.institutional_grade_type_id = igt.id");
        all_gt_instit_gt = cursor.fetchall()
    for grade_type_id, instit_grade_type_name in all_gt_instit_gt:
        key = get_key_from_value_institu_great_type_enum(instit_grade_type_name)
        with connection.cursor() as cursor:
            cursor.execute("update reference_gradetype set institutional_grade_type_enum = %s where id= %s ", [key, grade_type_id])


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0011_add_field_gtype_to_enum'),
    ]

    operations = [
        migrations.RunPython(move_fk_to_enum),
        migrations.RemoveField(
            model_name='gradetype',
            name='institutional_grade_type',
        ),
        migrations.RenameField(
            model_name='gradetype',
            old_name='institutional_grade_type_enum',
            new_name='institutional_grade_type'
        ),
        migrations.DeleteModel(
            name='InstitutionalGradeType',
        ),
    ]