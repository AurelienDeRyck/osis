##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import models
from django.contrib import admin


class LearningClassAdmin(admin.ModelAdmin):
    list_display = ('learning_component',)
    fieldsets = ((None, {'fields': ('learning_component',)}),)
    search_fields = ['acronym']


class LearningClass(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    learning_component = models.ForeignKey('LearningComponent')


def find_by_id(learning_class_id):
    return LearningClass.objects.get(pk=learning_class_id)


def find_by_ids(learning_class_ids):
    return LearningClass.objects.filter(pk__in=learning_class_ids)


def search(acronym=None):
    queryset = LearningClass.objects

    if acronym:
        queryset = queryset.filter(acronym=acronym)

    return queryset

