##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from base.models.enums import learning_unit_year_subtypes


class GroupElementYearAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child_branch', 'child_leaf',)
    fieldsets = ((None, {'fields': ('parent', 'child_branch', 'child_leaf',)}),)
    raw_id_fields = ('parent', 'child_branch', 'child_leaf',)


class GroupElementYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    parent = models.ForeignKey('EducationGroupYear', related_name='parent', blank=True, null=True)
    child_branch = models.ForeignKey('EducationGroupYear', related_name='child_branch', blank=True, null=True)
    child_leaf = models.ForeignKey('LearningUnitYear', related_name='child_leaf', blank=True, null=True)

    def is_deletable(self, msg):
        if self.parent:
            subtype = _('The learning unit') if self.child_leaf.subtype == learning_unit_year_subtypes.FULL else _('The partim')
            msg.append(
                _('%(subtype)s %(acronym)s is included in the group %(group)s of the program %(program)s for the year %(year)s')
                % {'subtype': subtype,
                   'acronym': self.child_leaf.acronym,
                   'group': self.parent.acronym,
                   'program': self.parent.education_group_type,
                   'year': self.child_leaf.academic_year})

        return not msg
