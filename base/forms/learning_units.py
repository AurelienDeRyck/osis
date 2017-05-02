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
from django import forms
from base import models as mdl
from django.core.exceptions import ValidationError
from base.enums import learning_unit_year_status
from base.enums import learning_unit_year_types


class LearningUnitYearForm(forms.Form):
    academic_year = forms.CharField(max_length=10, required=False)
    acronym = forms.CharField(widget=forms.TextInput(attrs={'size': '10', 'class': 'form-control'}),
                              max_length=20, required=False)
    keyword = forms.CharField(widget=forms.TextInput(attrs={'size': '10', 'class': 'form-control'}),
                              max_length=20, required=False)
    type = forms.CharField(
        widget=forms.Select(choices=learning_unit_year_types.LEARNING_UNIT_YEAR_TYPES,
                            attrs={'class' : 'form-control'}),
        required=False
    )
    status = forms.CharField(
        widget=forms.Select(choices=learning_unit_year_status.LEARNING_UNIT_YEAR_STATUS,
                            attrs={'class': 'form-control'}),
        required=False
    )

    def clean(self):
        clean_data = self.cleaned_data
        is_valid_search(**clean_data)
        return clean_data

    def get_learning_units(self):
        clean_data = self.cleaned_data

        return mdl.learning_unit_year.search(academic_year_id=clean_data.get('academic_year'),
                                             acronym=clean_data.get('acronym'),
                                             title=clean_data.get('keyword'),
                                             type=clean_data.get('type'),
                                             status=clean_data.get('status'))


def is_valid_search(**filter):
    # Must have a least one filter full
    nb_filter_set = sum(1 for value in filter.values() if value and value != 'NONE')
    if not nb_filter_set:
        raise ValidationError('LU_ERRORS_INVALID_SEARCH')

    # Academic year or learning unit acronym must be fill in
    academic_year = filter.get('academic_year')
    learning_unit_acronym = filter.get('acronym')
    if not academic_year and not learning_unit_acronym:
        raise ValidationError('LU_ERRORS_ACADEMIC_YEAR_REQUIRED')
