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
from django.db import transaction
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from base.models.enums import entity_container_year_link_type as entity_types
from base.models.enums.component_type import PRACTICAL_EXERCISES, LECTURING

ENTITY_TYPES_VOLUME = [
    entity_types.REQUIREMENT_ENTITY,
    entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1,
    entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
]


class EmptyField(forms.CharField):
    widget = forms.HiddenInput

    def __init__(self, label):
        super().__init__(label=label, required=False)


class VolumeField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_digits=6, decimal_places=2, min_value=0, **kwargs)


class VolumeEditionForm(forms.Form):

    requirement_entity_key = 'volume_' + entity_types.REQUIREMENT_ENTITY.lower()
    additional_requirement_entity_1_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1.lower()
    additional_requirement_entity_2_key = 'volume_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2.lower()

    volume_total = VolumeField(label=_('total_volume_voltot'), help_text=_('total_volume'))
    equal_field_1 = EmptyField(label='=')
    volume_q1 = VolumeField(label=_('partial_volume_1Q'), help_text=_('partial_volume_1'))
    add_field = EmptyField(label='+')
    volume_q2 = VolumeField(label=_('partial_volume_2Q'), help_text=_('partial_volume_2'))
    mult_field = EmptyField(label='*')
    planned_classes = forms.IntegerField(label=_('planned_classes_pc'), help_text=_('planned_classes'), min_value=0)
    equal_field_2 = EmptyField(label='=')

    _post_errors = []
    _parent_data = {}

    def __init__(self, *args, **kwargs):
        self.component = kwargs.pop('component')
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.entities = kwargs.pop('entities')

        self.title = self.component.acronym
        self.title_help = _(self.component.type) + ' ' if self.component.type else ''
        self.title_help += self.component.acronym

        super().__init__(*args, **kwargs)

        # Append dynamic fields
        for key, entity in self.entities.items():
            self.fields['volume_' + key.lower()] = VolumeField(
                label=entity.acronym, help_text=entity.title)

        self.fields['equal_field_3'] = EmptyField(label='=')

        self.fields['volume_total_requirement_entities'] = VolumeField(
            label=_('vol_charge'), help_text=_('total_volume_charge'))

    def clean(self):
        cleaned_data = super().clean().copy()

        self._check_tot_annual_equal_to_q1_q2(cleaned_data)
        self._check_tot_req_entities_equal_to_tot_annual_mult_cp(cleaned_data)
        self._check_tot_req_entities_equal_to_vol_req_entity(cleaned_data)

    def _check_tot_annual_equal_to_q1_q2(self, cleaned_data):
        total_annual = cleaned_data.get('volume_total', 0)
        q1 = cleaned_data.get('volume_q1', 0)
        q2 = cleaned_data.get('volume_q2', 0)

        if total_annual != (q1 + q2):
            self.add_error("volume_total", _('vol_tot_not_equal_to_q1_q2'))

    def _check_tot_req_entities_equal_to_vol_req_entity(self, cleaned_data):
        requirement_entity = cleaned_data.get(self.requirement_entity_key, 0)
        # Optional fields
        additional_requirement_entity_1 = cleaned_data.get(self.additional_requirement_entity_1_key, 0)
        additional_requirement_entity_2 = cleaned_data.get(self.additional_requirement_entity_2_key, 0)
        total = requirement_entity + additional_requirement_entity_1 + additional_requirement_entity_2

        if cleaned_data.get('volume_total_requirement_entities') != total:
            error_msg = ' + '.join([self.entities.get(t).acronym for t in ENTITY_TYPES_VOLUME if self.entities.get(t)])
            error_msg += ' = {}'.format(_('vol_charge'))
            self.add_error("volume_total_requirement_entities", error_msg)

    def _check_tot_req_entities_equal_to_tot_annual_mult_cp(self, cleaned_data):
        total_annual = cleaned_data.get('volume_total', 0)
        cp = cleaned_data.get('planned_classes', 0)
        total_requirement_entities = cleaned_data.get('volume_total_requirement_entities', 0)

        if total_requirement_entities != (total_annual * cp):
            self.add_error('volume_total_requirement_entities', _('vol_tot_req_entities_not_equal_to_vol_tot_mult_cp'))

    def validate_parent_partim_component(self, parent_data):
        self._parent_data = parent_data

        self._compare('volume_total', 'vol_tot_full_must_be_greater_than_partim', lower_or_equal=True)
        self._compare('volume_q1', 'vol_q1_full_must_be_greater_or_equal_to_partim')
        self._compare('volume_q2', 'vol_q2_full_must_be_greater_or_equal_to_partim')
        self._compare('planned_classes', 'planned_classes_full_must_be_greater_or_equal_to_partim')
        self._compare(self.requirement_entity_key, 'entity_requirement_full_must_be_greater_or_equal_to_partim')
        self._compare_additional_entities(self.additional_requirement_entity_1_key)
        self._compare_additional_entities(self.additional_requirement_entity_2_key)

        return self.errors

    def _compare_additional_entities(self, key):
        # Verify if we have additional_requirement entity
        if key in self._parent_data and key in self.cleaned_data:
            self._compare(key, 'entity_requirement_full_must_be_greater_or_equal_to_partim')

    def _compare(self, key, msg, lower_or_equal=False):
        partim_data = self.cleaned_data or self.initial

        if lower_or_equal:
            condition = self._parent_data[key] <= partim_data[key]
        else:
            condition = self._parent_data[key] < partim_data[key]

        if condition:
            self.add_error(key, _(msg))

    def save(self):
        if self.changed_data:
            self.component.hourly_volume_partial = self.cleaned_data['volume_q1']
            self.component.planned_classes = self.cleaned_data['planned_classes']
            self.component.save()
            self._save_requirement_entities(self.component.entity_components_year)

    def _save_requirement_entities(self, entity_components_year):
        for ecy in entity_components_year:
            link_type = ecy.entity_container_year.type
            repartition_volume = self.cleaned_data.get('volume_' + link_type.lower())

            if repartition_volume is None:
                continue

            ecy.repartition_volume = repartition_volume
            ecy.save()


class VolumeEditionBaseFormset(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year')
        self.components = list(self.learning_unit_year.components.keys())
        self.components_values = list(self.learning_unit_year.components.values())

        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['learning_unit_year'] = self.learning_unit_year
        kwargs['component'] = self.components[index]
        kwargs['initial'] = self._clean_component_keys(self.components_values[index])
        kwargs['entities'] = self.learning_unit_year.entities
        return kwargs

    @staticmethod
    def _clean_component_keys(component_dict):
        # Field's name must be in lowercase
        return {k.lower(): v for k, v in component_dict.items()}

    def validate_parent_partim(self, parent_formset):
        # Check CM
        is_cm_valid = self._validate_parent_partim_by_type(parent_formset, LECTURING)
        # Check TP
        is_tp_valid = self._validate_parent_partim_by_type(parent_formset, PRACTICAL_EXERCISES)
        return is_cm_valid and is_tp_valid

    def _validate_parent_partim_by_type(self, parent_formset, component_type):

        parent_form = parent_formset.get_form_by_type(component_type)
        partim_form = self.get_form_by_type(component_type)

        errors = partim_form.validate_parent_partim_component(parent_form.cleaned_data or parent_form.initial)

        return not errors

    def get_form_by_type(self, component_type):
        return next(form for form in self.forms if form.component.type == component_type)

    def save(self):
        for form in self.forms:
            form.save()


class VolumeEditionFormsetContainer:
    """
    Create and Manage a set of VolumeEditionFormsets
    """
    def __init__(self, request, learning_units):
        self.formsets = {}
        self.learning_units = learning_units
        self.parent = self.learning_units[0]
        self.request = request

        for learning_unit in learning_units:
            volume_edition_formset = formset_factory(
                form=VolumeEditionForm, formset=VolumeEditionBaseFormset, extra=len(learning_unit.components)
            )
            self.formsets[learning_unit] = volume_edition_formset(
                request.POST or None, learning_unit_year=learning_unit, prefix=learning_unit.acronym
            )

    def is_valid(self):
        if not self.request.POST:
            return False

        if not all([formset.is_valid() for formset in self.formsets.values()]):
            return False

        if not self._is_container_valid():
            return False

        return True

    def _is_container_valid(self):
        # Check consistency between formsets
        return all(self.formsets[luy].validate_parent_partim(self.formsets[self.parent]) for luy in self.formsets
                   if luy != self.parent)

    def save(self):
        with transaction.atomic():
            for formset in self.formsets.values():
                formset.save()

    @property
    def errors(self):
        errors = {}
        for formset in self.formsets.values():
            errors.update(self._get_formset_errors(formset))
        return errors

    @staticmethod
    def _get_formset_errors(formset):
        errors = {}
        for i, form_errors in enumerate(formset.errors):
            for name, error in form_errors.items():
                errors["{}-{}-{}".format(formset.prefix, i, name)] = error
        return errors

