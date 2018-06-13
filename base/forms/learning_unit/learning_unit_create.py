##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.acronym_field import AcronymField, PartimAcronymField, split_acronym
from base.forms.utils.choice_field import add_blank
from base.models.campus import find_main_campuses
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.component_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITIES
from base.models.enums.learning_container_year_types import CONTAINER_TYPE_WITH_DEFAULT_COMPONENT, \
    LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL, INTERNSHIP
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear, MAXIMUM_CREDITS
from reference.models.language import find_all_languages

DEFAULT_ACRONYM_COMPONENT = {
    LECTURING: "CM1",
    PRACTICAL_EXERCISES: "TP1",
    None: "NT1"
}


def _get_default_components_type(container_type):
    """This function will return the default components type to create/update according to container type"""
    if container_type in CONTAINER_TYPE_WITH_DEFAULT_COMPONENT:
        return [LECTURING, PRACTICAL_EXERCISES]
    return [None]


def _create_learning_container_year_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_WITHOUT_EXTERNAL)


def _create_faculty_learning_container_type_list():
    return add_blank(LEARNING_CONTAINER_YEAR_TYPES_FOR_FACULTY)


class LearningUnitModelForm(forms.ModelForm):

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.start_year = kwargs.pop('start_year')
        return super().save(**kwargs)

    class Meta:
        model = LearningUnit
        fields = ('faculty_remark', 'other_remark')
        widgets = {
            'faculty_remark': forms.Textarea(attrs={'rows': '5'}),
            'other_remark': forms.Textarea(attrs={'rows': '5'})
        }


# TODO Is it really useful ?
class LearningContainerModelForm(forms.ModelForm):
    class Meta:
        model = LearningContainer
        fields = ()


class LearningUnitYearModelForm(forms.ModelForm):

    def __init__(self, data, person, subtype, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

        self.instance.subtype = subtype
        self.person = person

        acronym = self.initial.get('acronym')
        if acronym:
            self.initial['acronym'] = split_acronym(acronym, subtype)

        if subtype == learning_unit_year_subtypes.PARTIM:
            self.fields['acronym'] = PartimAcronymField()
            self.fields['specific_title'].label = _('official_title_proper_to_partim')
            self.fields['specific_title_english'].label = _('official_english_title_proper_to_partim')

        if kwargs.get('instance'):
            self.fields['academic_year'].disabled = True

        self.fields['campus'].queryset = find_main_campuses()
        self.fields['language'].queryset = find_all_languages()

    class Meta:
        model = LearningUnitYear
        fields = ('academic_year', 'acronym', 'specific_title', 'specific_title_english', 'credits',
                  'session', 'quadrimester', 'status', 'internship_subtype', 'attribution_procedure',
                  'professional_integration', 'campus', 'language', 'periodicity')
        field_classes = {'acronym': AcronymField}
        error_messages = {
            'credits': {
                # Override unwanted DecimalField standard error messages
                'max_digits': _('Ensure this value is less than or equal to {max_value}.').format(
                    max_value=MAXIMUM_CREDITS),
                'max_whole_digits': _('Ensure this value is less than or equal to {max_value}.').format(
                    max_value=MAXIMUM_CREDITS)
            }
        }

    def post_clean(self, container_type):
        if container_type != INTERNSHIP and self.instance.internship_subtype:
            self.add_error("internship_subtype", _("This field cannot be set"))

        return not self.errors

    # TODO :: Move assignment to self.instance from save into __init__
    # TODO :: Make these kwarg to args (learning_container_year, learning_unit, ... are required args)
    def save(self, **kwargs):
        self.instance.learning_container_year = kwargs.pop('learning_container_year')
        self.instance.academic_year = self.instance.learning_container_year.academic_year
        self.instance.learning_unit = kwargs.pop('learning_unit')
        entity_container_years = kwargs.pop('entity_container_years')
        instance = super().save(**kwargs)
        for learn_unit_year in self._find_learning_units_year_family():
            self._save_learning_components(entity_container_years, learn_unit_year)
        return instance

    def _find_learning_units_year_family(self):
        return LearningUnitYear.objects.filter(learning_container_year=self.instance.learning_container_year)

    def _save_learning_components(self, entity_container_years, learning_unit_year):
        components_type = _get_default_components_type(self.instance.learning_container_year.container_type)
        for component_type in components_type:
            component, created = LearningComponentYear.objects.get_or_create(
                learningunitcomponent__learning_unit_year=learning_unit_year,
                type=component_type,
                defaults={
                    'acronym': DEFAULT_ACRONYM_COMPONENT[component_type],
                    'learning_container_year': learning_unit_year.learning_container_year
                }
            )
            self._save_learning_unit_component(component, learning_unit_year)
            self._save_entity_components_year(component, entity_container_years)

    @staticmethod
    def _save_learning_unit_component(component, learning_unit_year):
        return LearningUnitComponent.objects.get_or_create(learning_unit_year=learning_unit_year,
                                                           learning_component_year=component)

    @staticmethod
    def _save_entity_components_year(component, entity_container_years):
        requirement_entity_containers = filter(lambda ec: getattr(ec, 'type', None) in REQUIREMENT_ENTITIES,
                                               entity_container_years)
        for requirement_entity_container in requirement_entity_containers:
            EntityComponentYear.objects.get_or_create(entity_container_year=requirement_entity_container,
                                                      learning_component_year=component)


class LearningUnitYearPartimModelForm(LearningUnitYearModelForm):
    class Meta(LearningUnitYearModelForm.Meta):
        labels = {
            'specific_title': _('official_title_proper_to_partim'),
            'specific_title_english': _('official_english_title_proper_to_partim')
        }
        field_classes = {
            'acronym': PartimAcronymField
        }


class LearningContainerYearModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person')
        self.proposal = kwargs.pop('proposal', False)
        self.is_create_form = kwargs['instance'] is None
        super().__init__(*args, **kwargs)
        self.prepare_fields()

    def prepare_fields(self):
        self.fields['container_type'].widget.attrs = {'onchange': 'showInternshipSubtype()'}

        # Limit types for faculty_manager only if simple creation of learning_unit
        if self.person.is_faculty_manager() and not self.proposal and self.is_create_form:
            self.fields["container_type"].choices = _create_faculty_learning_container_type_list()
        else:
            self.fields["container_type"].choices = _create_learning_container_year_type_list()

    def save(self, **kwargs):
        self.instance.learning_container = kwargs.pop('learning_container')
        self.instance.acronym = kwargs.pop('acronym')
        self.instance.academic_year = kwargs.pop('academic_year')
        return super().save(**kwargs)

    class Meta:
        model = LearningContainerYear
        fields = ('container_type', 'common_title', 'common_title_english',
                  'type_declaration_vacant', 'team', 'is_vacant')

    def post_clean(self, specific_title):
        if not self.instance.common_title and not specific_title:
            self.add_error("common_title", _("must_set_common_title_or_specific_title"))

        return not self.errors
