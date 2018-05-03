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
from unittest import mock

import factory
import factory.fuzzy
from django.forms import model_to_dict
from django.http import QueryDict
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningUnitModelForm, EntityContainerFormset, LearningContainerYearModelForm, LearningContainerModelForm
from base.forms.learning_unit.learning_unit_create_2 import PartimForm, PARTIM_FORM_READ_ONLY_FIELD
from base.forms.utils import acronym_field
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_periodicity import ANNUAL, BIENNIAL_EVEN
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from django.test import TestCase
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningUnitModelForm, EntityContainerFormset, LearningContainerYearModelForm, LearningContainerModelForm
from base.models.enums import learning_unit_year_subtypes
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory

FULL_ACRONYM = 'LBIR1200'
SUBDIVISION_ACRONYM = 'A'


class LearningUnitPartimFormContextMixin(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing PARTIM FORM"""
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.generated_ac_years = GenerateAcademicYear(self.current_academic_year.year + 1,
                                                       self.current_academic_year.year + 10)

        # Creation of a LearingContainerYear and all related models
        self.learn_unit_structure = GenerateContainer(self.current_academic_year.year, self.current_academic_year.year)
        # Build in Generated Container [first index = start Generate Container ]
        self.generated_container_year = self.learn_unit_structure.generated_container_years[0]

        # Update Full learning unit year acronym
        self.learning_unit_year_full = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_full,
            academic_year=self.current_academic_year
        )
        self.learning_unit_year_full.acronym = FULL_ACRONYM
        self.learning_unit_year_full.learning_container_year.acronym = FULL_ACRONYM
        self.learning_unit_year_full.learning_container_year.save()
        self.learning_unit_year_full.save()

        # Update Partim learning unit year acronym
        self.learning_unit_year_partim = LearningUnitYear.objects.get(
            learning_unit=self.learn_unit_structure.learning_unit_partim,
            academic_year=self.current_academic_year,
            learning_container_year=self.learning_unit_year_full.learning_container_year
        )
        self.learning_unit_year_partim.acronym = FULL_ACRONYM + SUBDIVISION_ACRONYM
        self.learning_unit_year_partim.save()


class TestPartimFormInit(LearningUnitPartimFormContextMixin):
    """Unit tests for PartimForm.__init__()"""
    def test_subtype_is_partim(self):
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.current_academic_year)
        self.assertEqual(form.subtype, learning_unit_year_subtypes.PARTIM)

    def test_wrong_learning_unit_full_instance_args(self):
        wrong_lu_full = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_form(learning_unit_full=wrong_lu_full, academic_year=self.current_academic_year)

    def test_wrong_instance_args(self):
        wrong_instance = LearningUnitYearFactory()
        with self.assertRaises(AttributeError):
            _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                              academic_year=self.current_academic_year,
                              instance=wrong_instance)

    def test_model_forms_case_creation(self):
        form_classes_expected = [LearningUnitModelForm, LearningUnitYearModelForm, LearningContainerModelForm,
                                 LearningContainerYearModelForm, EntityContainerFormset]
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.current_academic_year)
        for cls in form_classes_expected:
            self.assertIsInstance(form.forms[cls], cls)

    def test_inherit_initial_values(self):
        """This test will check if field are pre-full in by value of full learning unit year"""
        expected_initials = {
            LearningUnitModelForm: {
                'periodicity': self.learning_unit_year_full.learning_unit.periodicity
            },
            LearningUnitYearModelForm: {
                'acronym': ['L', 'BIR1200', ''],
                'acronym_0': 'L',  # Multiwidget decomposition
                'acronym_1': 'BIR1200',
                'acronym_2': '',
                'academic_year': self.learning_unit_year_full.academic_year.id,
                'internship_subtype': self.learning_unit_year_full.internship_subtype,
                'attribution_procedure': self.learning_unit_year_full.attribution_procedure,
                'subtype': learning_unit_year_subtypes.PARTIM,  # Creation of partim
                'credits': self.learning_unit_year_full.credits,
                'session': self.learning_unit_year_full.session,
                'quadrimester': self.learning_unit_year_full.quadrimester,
                'status': self.learning_unit_year_full.status,
                'specific_title': self.learning_unit_year_full.specific_title,
                'specific_title_english': self.learning_unit_year_full.specific_title_english
            }
        }
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.current_academic_year)
        for form_class, initial in expected_initials.items():
            self.assertEqual(partim_form.forms[form_class].initial, initial)

    def test_instance_partim_values(self):
        partim = LearningUnitYearFactory(acronym='LBIR1200A', subtype=learning_unit_year_subtypes.PARTIM,
                                         learning_container_year=self.learning_unit_year_full.learning_container_year,
                                         academic_year=self.learning_unit_year_full.academic_year)

        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year,
                                        instance=partim.learning_unit)
        self.assertEqual(partim_form.forms[LearningUnitYearModelForm].initial['acronym'], ['L', 'BIR1200', 'A'])

    def test_disabled_fields(self):
        """This function will check if fields is disabled"""
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year)
        expected_disabled_fields = {
            'common_title', 'common_title_english',
            'requirement_entity', 'allocation_entity',
            'language', 'periodicity', 'campus',
            'academic_year', 'container_type', 'internship_subtype',
            'additional_requirement_entity_1', 'additional_requirement_entity_2'
        }
        all_fields = partim_form.fields.items()
        self.assertTrue(all(field.disabled == (field_name in expected_disabled_fields)
                            for field_name, field in all_fields))

    def test_form_cls_to_validate(self):
        """This function will ensure that only LearningUnitModelForm/LearningUnitYearModelForm is present
           in form_cls_to_validate"""
        partim_form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                        academic_year=self.learning_unit_year_full.academic_year)
        expected_form_cls = [LearningUnitModelForm, LearningUnitYearModelForm]
        self.assertEqual(partim_form.form_cls_to_validate, expected_form_cls)


class TestPartimFormIsValid(LearningUnitPartimFormContextMixin):
    """Unit tests for is_valid() """
    def _assert_equal_values(self, obj, dictionnary, fields_to_validate):
        for field in fields_to_validate:
            self.assertEqual(getattr(obj, field), dictionnary[field], msg='Error field = {}'.format(field))

    def test_creation_case_correct_post_data(self):
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'B',
            subtype=learning_unit_year_subtypes.PARTIM
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data)
        # The form should be valid
        self.assertTrue(form.is_valid(), form.errors)
        # In partim, we can only modify LearningUnitYearModelForm / LearningUnitModelForm
        self._test_learning_unit_model_form_instance(form, post_data)
        self._test_learning_unit_year_model_form_instance(form, post_data)
        # Inherit instance from learning unit year full
        self._test_learning_container_model_form_instance(form)
        self._test_learning_container_year_model_form_instance(form)
        self._test_entity_container_model_formset_instance(form)

    def test_partim_periodicity_annual_with_parent_biannual(self):
        a_new_learning_unit_partim = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'W',
            subtype=learning_unit_year_subtypes.PARTIM,
            credits=0,
            learning_container_year=self.learning_unit_year_full.learning_container_year,
        )
        a_new_learning_unit_partim.learning_unit.learning_container = self.learning_unit_year_full.learning_unit.learning_container
        a_new_learning_unit_partim.learning_unit.save()

        self.learning_unit_year_full.learning_unit.periodicity = BIENNIAL_EVEN
        self.learning_unit_year_full.learning_unit.save()

        post_data = get_valid_form_data(a_new_learning_unit_partim)
        post_data['periodicity'] = ANNUAL

        form = LearningUnitModelForm(data=post_data, instance=a_new_learning_unit_partim.learning_unit)

        # The form should be valid
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors.get('periodicity'),
                         [_('The periodicity of the partim must be the same as that of the parent')])

    def test_partim_periodicity_biannual_with_parent_annual(self):
        a_new_learning_unit_partim = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'W',
            subtype=learning_unit_year_subtypes.PARTIM,
            credits=0,
            learning_container_year=self.learning_unit_year_full.learning_container_year,
        )
        a_new_learning_unit_partim.learning_unit.learning_container = self.learning_unit_year_full.learning_unit.learning_container
        a_new_learning_unit_partim.learning_unit.save()

        self.learning_unit_year_full.learning_unit.periodicity = ANNUAL
        self.learning_unit_year_full.learning_unit.save()

        post_data = get_valid_form_data(a_new_learning_unit_partim)
        post_data['periodicity'] = BIENNIAL_EVEN

        form = LearningUnitModelForm(data=post_data, instance=a_new_learning_unit_partim.learning_unit)

        # The form should be valid
        self.assertTrue(form.is_valid(), form.errors)

    def _test_learning_unit_model_form_instance(self, partim_form, post_data):
        form_instance = partim_form.forms[LearningUnitModelForm]
        fields_to_validate = ['faculty_remark', 'other_remark']
        self._assert_equal_values(form_instance.instance, post_data, fields_to_validate)
        # Periodicity inherit from parent [Cannot be modify by user]
        self.assertEqual(form_instance.instance.periodicity,
                         self.learning_unit_year_full.learning_unit.periodicity)

    def _test_learning_unit_year_model_form_instance(self, partim_form, post_data):
        form_instance = partim_form.forms[LearningUnitYearModelForm]
        fields_to_validate = ['specific_title', 'specific_title_english', 'credits',
                              'session', 'quadrimester', 'status', 'subtype', ]
        self._assert_equal_values(form_instance.instance, post_data, fields_to_validate)
        self.assertEqual(form_instance.instance.acronym, FULL_ACRONYM + 'B')

        # Academic year should be the same as learning unit full [Inherit field]
        self.assertEqual(form_instance.instance.academic_year.id, self.learning_unit_year_full.academic_year.id)

    def _test_learning_container_model_form_instance(self, partim_form):
        """In this test, we ensure that the instance of learning container model form inherit
           from full learning container """
        form_instance = partim_form.forms[LearningContainerModelForm]
        self.assertEqual(form_instance.instance,
                         self.learning_unit_year_full.learning_container_year.learning_container)

    def _test_learning_container_year_model_form_instance(self, partim_form):
        """ In this test, we ensure that the instance of learning container year model form inherit
            from full learning container year """
        form_instance = partim_form.forms[LearningContainerYearModelForm]
        self.assertEqual(form_instance.instance,
                         self.learning_unit_year_full.learning_container_year)

    def _test_entity_container_model_formset_instance(self, partim_form):
        """ In this test, we ensure that the instance of learning container year model form inherit
            from full learning container year """
        formset_instance = partim_form.forms[EntityContainerFormset]
        self.assertEqual(formset_instance.instance,
                         self.learning_unit_year_full.learning_container_year)
        # Test expected instance
        expected_instance_form = [
            self.generated_container_year.requirement_entity_container_year,
            self.generated_container_year.allocation_entity_container_year,
            self.generated_container_year.additionnal_1_entity_container_year,
            self.generated_container_year.addtionnal_2_entity_container_year,
        ]
        for index, form in enumerate(formset_instance.forms):
            self.assertEqual(expected_instance_form[index], form.instance)

    @mock.patch('base.forms.learning_unit.learning_unit_create.LearningUnitModelForm.is_valid',
                side_effect=lambda *args: False)
    def test_creation_case_wrong_learning_unit_data(self, mock_is_valid):
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'B',
            subtype=learning_unit_year_subtypes.PARTIM
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data)
        self.assertFalse(form.is_valid())


class TestPartimFormSave(LearningUnitPartimFormContextMixin):
    """Unit tests for save() for save"""
    @mock.patch('base.forms.learning_unit.learning_unit_create.LearningUnitModelForm.save')
    @mock.patch('base.forms.learning_unit.learning_unit_create.LearningUnitYearModelForm.save')
    @mock.patch('base.forms.learning_unit.learning_unit_create_2.PartimForm._get_entity_container_year',
                side_effect=lambda *args: [])
    def test_save_method_mocked(self, mock_get_entity_container_year, mock_luy_form_save, mock_lu_form_save):
        learning_container_year_full = self.learning_unit_year_full.learning_container_year
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=FULL_ACRONYM + 'C',
            subtype=learning_unit_year_subtypes.PARTIM
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)
        start_year = self.learning_unit_year_full.academic_year.year

        # Define return mock value
        mock_luy_form_save.return_value = a_new_learning_unit_partim
        mock_lu_form_save.return_value = a_new_learning_unit_partim.learning_unit
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data, instance=None)
        self.assertTrue(form.is_valid())
        form.save()
        # Ensure call to learning unit model form is done
        self.assertTrue(mock_lu_form_save.called)
        mock_lu_form_save.assert_called_once_with(
            start_year=start_year,
            learning_container=learning_container_year_full.learning_container,
            commit=True
        )
        # Ensure call to learning unit year model form is done
        self.assertTrue(mock_get_entity_container_year.called)
        self.assertTrue(mock_luy_form_save.called)
        mock_luy_form_save.assert_called_once_with(
            learning_container_year=learning_container_year_full,
            entity_container_years=[],
            learning_unit=a_new_learning_unit_partim.learning_unit,
            commit=True
        )

    def test_save_method_create_new_instance(self):
        partim_acronym = FULL_ACRONYM + 'C'
        a_new_learning_unit_partim = LearningUnitYearFactory.build(
            academic_year=self.current_academic_year,
            acronym=partim_acronym,
            subtype=learning_unit_year_subtypes.PARTIM
        )
        post_data = get_valid_form_data(a_new_learning_unit_partim)

        form = _instanciate_form(
            learning_unit_full=self.learning_unit_year_full.learning_unit,
            academic_year=self.learning_unit_year_full.academic_year,
            post_data=post_data, instance=None
        )
        self.assertTrue(form.is_valid())
        form.save()

        # Check all related object is created
        self.assertEqual(LearningUnitYear.objects.filter(acronym=partim_acronym,
                                                         academic_year=self.current_academic_year).count(), 1)
        self.assertEqual(LearningUnit.objects.filter(learningunityear__acronym=partim_acronym).count(), 1)

    def test_save_method_update_instance(self):
        post_data = get_valid_form_data(self.learning_unit_year_partim)
        update_fields_luy_model = {
            'credits': 2.5,
            'specific_title': factory.fuzzy.FuzzyText(length=15).fuzz(),
            'specific_title_english': factory.fuzzy.FuzzyText(length=15).fuzz(),
        }
        post_data.update(update_fields_luy_model)
        update_fields_lu_model = {
            'faculty_remark': factory.fuzzy.FuzzyText(length=15).fuzz(),
            'other_remark': factory.fuzzy.FuzzyText(length=15).fuzz()
        }
        post_data.update(update_fields_lu_model)

        form = _instanciate_form(
            learning_unit_full=self.learning_unit_year_full.learning_unit,
            academic_year=self.learning_unit_year_full.academic_year,
            post_data=post_data,
            instance=self.learning_unit_year_partim.learning_unit
        )
        self.assertTrue(form.is_valid(), msg=form.errors)
        form.save()

        # Refresh learning unit year
        self.learning_unit_year_partim.refresh_from_db()
        # Check learning unit year update
        learning_unit_year_dict = model_to_dict(self.learning_unit_year_partim)
        for field, value in update_fields_luy_model.items():
            self.assertEqual(learning_unit_year_dict[field], value)

        # Check learning unit update
        self.learning_unit_year_partim.learning_unit.refresh_from_db()
        learning_unit_dict = model_to_dict(self.learning_unit_year_partim.learning_unit)
        for field, value in update_fields_lu_model.items():
            self.assertEqual(learning_unit_dict[field], value)

    def test_save_partim_without_container(self):
        post_data = get_valid_form_data(self.learning_unit_year_partim)
        parent_acronym = self.learning_unit_year_partim.learning_container_year.acronym
        partim_acronym = parent_acronym + 'X'
        post_data['acronym_2'] = partim_acronym[-1]
        post_data['credits'] = 2.5

        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 post_data=post_data,
                                 instance=self.learning_unit_year_partim.learning_unit)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        # Refresh learning unit year
        self.learning_unit_year_partim.refresh_from_db()
        self.assertEqual(self.learning_unit_year_partim.acronym, partim_acronym)
        self.assertEqual(self.learning_unit_year_partim.learning_container_year.acronym, parent_acronym)

    def test_disable_fields_partim(self):
        form = _instanciate_form(learning_unit_full=self.learning_unit_year_full.learning_unit,
                                 academic_year=self.learning_unit_year_full.academic_year,
                                 instance=self.learning_unit_year_partim.learning_unit)
        disabled_fields = {key for key, value in form.fields.items() if value.disabled == True}
        # acronym_0 and acronym_1 are disabled in the widget, not in the field
        disabled_fields.update({'acronym_0', 'acronym_1'})
        self.assertEqual(disabled_fields, PARTIM_FORM_READ_ONLY_FIELD)


def get_valid_form_data(learning_unit_year_partim):
    acronym_splited = acronym_field.split_acronym(learning_unit_year_partim.acronym)
    post_data = {
        # Learning unit year data model form
        'acronym_2': acronym_splited[2],
        'subtype': learning_unit_year_partim.subtype,
        'specific_title': learning_unit_year_partim.specific_title,
        'specific_title_english': learning_unit_year_partim.specific_title_english,
        'credits': learning_unit_year_partim.credits,
        'session': learning_unit_year_partim.session,
        'quadrimester': learning_unit_year_partim.quadrimester,
        'status': learning_unit_year_partim.status,

        # Learning unit data model form
        'periodicity': learning_unit_year_partim.learning_unit.periodicity,
        'faculty_remark': learning_unit_year_partim.learning_unit.faculty_remark,
        'other_remark': learning_unit_year_partim.learning_unit.other_remark,
    }
    qdict = QueryDict('', mutable=True)
    qdict.update(post_data)
    return qdict


def _instanciate_form(learning_unit_full, academic_year, post_data=None, instance=None):
    person = PersonFactory()
    return PartimForm(person, learning_unit_full, academic_year, data=post_data,
                      learning_unit_instance=instance)
