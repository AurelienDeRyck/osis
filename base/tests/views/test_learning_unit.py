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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from decimal import Decimal
from unittest import mock

import factory.fuzzy
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

import base.business.learning_unit
from base.business import learning_unit as learning_unit_business
from base.forms.learning_unit_create import CreateLearningUnitYearForm, CreatePartimForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm
from base.forms.learning_unit_search import SearchForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.forms.learning_units import LearningUnitYearForm
from base.models import learning_unit_component
from base.models import learning_unit_component_class
from base.models.academic_year import AcademicYear
from base.models.enums import entity_container_year_link_type, active_status
from base.models.enums import internship_subtypes
from base.models.enums import learning_container_year_types, organization_type, entity_type
from base.models.enums import learning_unit_periodicity
from base.models.enums import learning_unit_year_quadrimesters
from base.models.enums import learning_unit_year_session
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_container_year_types import MASTER_THESIS
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import FACULTY_MANAGER_GROUP
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_component_class import LearningUnitComponentClassFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from base.views.learning_unit import compute_partim_form_initial_data, _get_post_data_without_read_only_field, \
    learning_unit_components, learning_class_year_edit, _compare_model_with_initial_value, \
    _get_the_old_value, _is_foreign_key, END_FOREIGN_KEY_NAME, VALUES_WHICH_NEED_TRANSLATION, \
    _get_str_representing_old_data_from_foreign_key, LABEL_VALUE_BEFORE_PROPROSAL, \
    _replace_key_of_foreign_key, _check_differences, _get_difference_of_proposal, _get_old_value_of_foreign_key, \
    NO_PREVIOUS_VALUE, _has_changed_entity
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from osis_common.document import xls_build
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from django.apps import apps


class LearningUnitViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_year_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                         end_date=today.replace(year=today.year + 2),
                                                         year=today.year + 1)
        self.academic_year_2 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 2),
                                                         end_date=today.replace(year=today.year + 3),
                                                         year=today.year + 2)
        self.academic_year_3 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 3),
                                                         end_date=today.replace(year=today.year + 4),
                                                         year=today.year + 3)
        self.academic_year_4 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 4),
                                                         end_date=today.replace(year=today.year + 5),
                                                         year=today.year + 4)
        self.academic_year_5 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 5),
                                                         end_date=today.replace(year=today.year + 6),
                                                         year=today.year + 5)
        self.academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                         end_date=today.replace(year=today.year + 7),
                                                         year=today.year + 6)
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        super(AcademicYear, self.academic_year_1).save()
        super(AcademicYear, self.academic_year_2).save()
        super(AcademicYear, self.academic_year_3).save()
        super(AcademicYear, self.academic_year_4).save()
        super(AcademicYear, self.academic_year_5).save()
        super(AcademicYear, self.academic_year_6).save()
        self.learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year)
        self.learning_component_yr = LearningComponentYearFactory(learning_container_year=self.learning_container_yr)
        self.organization = OrganizationFactory(type=organization_type.MAIN)
        self.country = CountryFactory()
        self.entity = EntityFactory(country=self.country, organization=self.organization)
        self.entity_2 = EntityFactory(country=self.country, organization=self.organization)
        self.entity_3 = EntityFactory(country=self.country, organization=self.organization)
        self.entity_container_yr = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                              type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                              entity=self.entity)
        self.entity_container_yr_2 = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                                type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                                entity=self.entity_2)
        self.entity_container_yr_3 = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                                type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                                entity=self.entity_3)
        self.entity_version = EntityVersionFactory(entity=self.entity, entity_type=entity_type.SCHOOL,
                                                   start_date=today - datetime.timedelta(days=1),
                                                   end_date=today.replace(year=today.year + 1))

        self.campus = CampusFactory(organization=self.organization, is_administration=True)
        self.language = LanguageFactory(code='FR')
        self.a_superuser = SuperUserFactory()
        self.person = PersonFactory(user=self.a_superuser)
        PersonEntityFactory(person=self.person, entity=self.entity)
        PersonEntityFactory(person=self.person, entity=self.entity_2)
        PersonEntityFactory(person=self.person, entity=self.entity_3)
        self.client.force_login(self.a_superuser)

    @mock.patch('base.views.layout.render')
    def test_learning_units(self, mock_render):
        request_factory = RequestFactory()

        request = request_factory.get(reverse('learning_units'))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['academic_years']), 7)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search(self, mock_render):
        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_units'))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['academic_years'].count(), 7)
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['types']),
                         len(learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES))
        self.assertEqual(len(context['container_types']),
                         len(learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES))
        self.assertTrue(context['experimental_phase'])
        self.assertEqual(context['learning_units'], [])

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_acronym_filtering(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': active_status.ACTIVE,
            'acronym': 'LBIR'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 3)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_by_acronym_with_valid_regex(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'acronym': '^DRT.+A'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 1)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_by_acronym_with_invalid_regex(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': active_status.ACTIVE,
            'acronym': '^LB(+)2+'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['form'].errors['acronym'], [_('LU_ERRORS_INVALID_REGEX_SYNTAX')])

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ENVI'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 1)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity_and_subord(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 6)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_service_course(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        from base.views.learning_unit import learning_units_service_course

        request = request_factory.get(reverse(learning_units_service_course), data=filter_data)
        request.user = self.a_superuser

        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        learning_units_service_course(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 0)

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_read(self, mock_program_manager, mock_render):
        mock_program_manager.return_value = True

        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year)

        request = self.create_learning_unit_request(learning_unit_year)

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(context['learning_unit_year'], learning_unit_year)

    def test_learning_unit__with_faculty_manager_when_can_edit_end_date(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year, container_type=learning_container_year_types.OTHER_COLLECTIVE)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        person_entity.person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_of_type_partim_with_faculty_manager(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year, container_type=learning_container_year_types.COURSE)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.PARTIM)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        person_entity.person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_with_faculty_manager_when_cannot_edit_end_date(self):
        learning_container_year = \
            LearningContainerYearFactory(academic_year=self.current_academic_year,
                                         container_type=learning_container_year_types.COURSE)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        entity_container = EntityContainerYearFactory(learning_container_year=learning_container_year,
                                                      type=entity_container_year_link_type.REQUIREMENT_ENTITY)

        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()

        person_entity = PersonEntityFactory(entity=entity_container.entity)
        person_entity.person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        url = reverse("learning_unit", args=[learning_unit_year.id])
        self.client.force_login(person_entity.person.user)

        response = self.client.get(url)
        self.assertEqual(response.context["can_edit_date"], False)

    def test_get_components_no_learning_container_yr(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.assertEqual(len(learning_unit_business.get_same_container_year_components(learning_unit_year, False)), 0)

    def test_get_components_with_classes(self):
        l_container = LearningContainerFactory()
        l_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                        common_title="LC-98998", learning_container=l_container)
        l_component_year = LearningComponentYearFactory(learning_container_year=l_container_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=l_container_year)

        components = learning_unit_business.get_same_container_year_components(learning_unit_year, True)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0]['learning_component_year'].classes), 2)

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_get_partims_identification_tabs(self, mock_program_manager, mock_render):
        mock_program_manager.return_value = True

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210A",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210B",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210F",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )

        request = self.create_learning_unit_request(learning_unit_year)

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(len(context['learning_container_year_partims']), 3)

    @mock.patch('base.views.layout.render')
    def test_learning_unit_formation(self, mock_render):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr)
        request_factory = RequestFactory()

        request = request_factory.get(reverse('learning_unit_formations', args=[learning_unit_year.id]))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_unit_formations

        learning_unit_formations(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/formations.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(context['learning_unit_year'], learning_unit_year)

    def test_learning_unit_usage_two_usages(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLA',
                                                     quadrimester='Q1',
                                                     learning_container_year=learning_container_yr)
        learning_unit_yr_2 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLB',
                                                     learning_container_year=learning_container_yr,
                                                     quadrimester=None)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_2,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_business._learning_unit_usage(learning_component_yr), 'LBIOLA (Q1), LBIOLB (?)')

    def test_learning_unit_usage_with_complete_LU(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOL', quadrimester='Q1&2',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_business._learning_unit_usage(learning_component_yr), 'LBIOL (Q1&2)')

    def test_learning_unit_usage_by_class_with_complete_LU(self):
        academic_year = AcademicYearFactory(year=2016)
        learning_container_yr = LearningContainerYearFactory(academic_year=academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=academic_year,
                                                     acronym='LBIOL',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        learning_unit_component = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                                               learning_component_year=learning_component_yr)
        learning_class_year = LearningClassYearFactory(learning_component_year=learning_component_yr)
        LearningUnitComponentClassFactory(learning_unit_component=learning_unit_component,
                                          learning_class_year=learning_class_year)
        self.assertEqual(learning_unit_business._learning_unit_usage_by_class(learning_class_year), 'LBIOL')

    def test_component_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)

    def test_component_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1"})
        self.assertRaises(ObjectDoesNotExist, learning_unit_component.LearningUnitComponent.objects.filter(
            pk=learning_unit_compnt.id).first())

    def test_component_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1", "used_by": "on"})

        self.assertTrue(learning_unit_component.find_by_learning_component_year(self.learning_component_yr).exists())

    def _prepare_context_learning_units_search(self):
        # Create a structure [Entity / Entity version]
        ssh_entity = EntityFactory(country=self.country)
        ssh_entity_v = EntityVersionFactory(acronym="SSH", end_date=None, entity=ssh_entity)

        agro_entity = EntityFactory(country=self.country)
        envi_entity = EntityFactory(country=self.country)
        ages_entity = EntityFactory(country=self.country)
        agro_entity_v = EntityVersionFactory(entity=agro_entity, parent=ssh_entity_v.entity, acronym="AGRO",
                                             end_date=None)
        envi_entity_v = EntityVersionFactory(entity=envi_entity, parent=agro_entity_v.entity, acronym="ENVI",
                                             end_date=None)
        ages_entity_v = EntityVersionFactory(entity=ages_entity, parent=agro_entity_v.entity, acronym="AGES",
                                             end_date=None)

        espo_entity = EntityFactory(country=self.country)
        drt_entity = EntityFactory(country=self.country)
        espo_entity_v = EntityVersionFactory(entity=espo_entity, parent=ssh_entity_v.entity, acronym="ESPO",
                                             end_date=None)
        drt_entity_v = EntityVersionFactory(entity=drt_entity, parent=ssh_entity_v.entity, acronym="DRT",
                                            end_date=None)

        # Create UE and put entity charge [AGRO]
        l_container_yr = LearningContainerYearFactory(acronym="LBIR1100", academic_year=self.current_academic_year,
                                                      container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr, entity=agro_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="LBIR1100", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="LBIR1100A", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100B", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100C", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM,
                                status=False)

        # Create another UE and put entity charge [ENV]
        l_container_yr_2 = LearningContainerYearFactory(acronym="CHIM1200", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_2, entity=envi_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="CHIM1200", learning_container_year=l_container_yr_2,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [DRT]
        l_container_yr_3 = LearningContainerYearFactory(acronym="DRT1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_3, entity=drt_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="DRT1500", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="DRT1500A", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)

        # Create another UE and put entity charge [ESPO]
        l_container_yr_4 = LearningContainerYearFactory(acronym="ESPO1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.DISSERTATION)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=espo_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="ESPO1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [AGES]
        l_container_yr_4 = LearningContainerYearFactory(acronym="AGES1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.MASTER_THESIS)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=ages_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="AGES1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

    def test_class_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                     learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse(learning_class_year_edit, args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)

    def test_class_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse(learning_class_year_edit, args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})

        self.assertTrue(learning_unit_component_class.search(learning_unit_compnt, learning_class_yr).exists())

    def test_class_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)
        a_link = LearningUnitComponentClassFactory(learning_unit_component=learning_unit_compnt,
                                                   learning_class_year=learning_class_yr)

        response = self.client.post('{}?{}&{}'.format(reverse(learning_class_year_edit, args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={})

        self.assertFalse(learning_unit_component_class.LearningUnitComponentClass.objects.filter(pk=a_link.id).exists())

    def get_base_form_data(self):
        data = self.get_common_data()
        data.update(self.get_learning_unit_data())
        data['internship_subtype'] = internship_subtypes.TEACHING_INTERNSHIP
        return data

    def get_base_partim_form_data(self, original_learning_unit_year):
        data = self.get_common_data()
        data.update(self.get_partim_data(original_learning_unit_year))
        data['specific_title'] = "Partim partial title"
        return data

    def get_common_data(self):
        return {
            "container_type": learning_container_year_types.COURSE,
            "academic_year": self.current_academic_year.id,
            "status": True,
            "periodicity": learning_unit_periodicity.ANNUAL,
            "credits": "5",
            "campus": self.campus.id,
            "common_title": "Common UE title",
            "common_title_english": "Common English UUE title",
            "requirement_entity": self.entity_version.id,
            "allocation_entity": self.entity_version.id,
            "additional_requirement_entity_1": self.entity_version.id,
            "additional_requirement_entity_2": self.entity_version.id,
            "language": self.language.id,
            "session": learning_unit_year_session.SESSION_P23,
            "faculty_remark": "faculty remark",
            "other_remark": "other remark"
        }

    def get_learning_unit_data(self):
        return {'first_letter': 'L',
                'acronym': 'TAU2000',
                "subtype": learning_unit_year_subtypes.FULL}

    def get_partim_data(self, original_learning_unit_year):
        return {
            'first_letter': original_learning_unit_year.acronym[:1],
            'acronym': original_learning_unit_year.acronym[1:],
            'partim_character': factory.fuzzy.FuzzyText(length=1).fuzz(),
            "subtype": learning_unit_year_subtypes.PARTIM
        }

    def get_valid_data(self):
        return self.get_base_form_data()

    def get_faulty_acronym(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym"] = "TA200"
        return faultydict

    def get_existing_acronym(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym"] = "DRT2018"
        return faultydict

    def get_empty_internship_subtype(self):
        faultydict = dict(self.get_valid_data())
        faultydict["container_type"] = learning_container_year_types.INTERNSHIP
        faultydict["internship_subtype"] = ""
        return faultydict

    def get_empty_acronym(self):
        faultyDict = dict(self.get_valid_data())
        faultyDict["acronym"] = ""
        return faultyDict

    def get_faulty_requirement_entity(self):
        """We will create an entity + entity version that user cannot create on it"""
        entity = EntityFactory(country=self.country, organization=self.organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, end_date=None,
                                              start_date=datetime.date.today())
        faultydict = dict(self.get_valid_data())
        faultydict['requirement_entity'] = entity_version.id
        return faultydict

    def test_learning_unit_year_form(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        url = reverse('learning_unit_year_add')
        response = self.client.post(url, data=self.get_base_form_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 7)

    def test_create_learning_unit_year_requirement_entity_not_allowed(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_faulty_requirement_entity())
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('requirement_entity' in form.errors)

    def test_learning_unit_creation_form_with_valid_data(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.cleaned_data, form.errors)
        self.assertEqual(form.cleaned_data['acronym'], "LTAU2000")

    def test_learning_unit_creation_form_with_empty_acronym(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_empty_acronym())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['acronym'], [_('field_is_required')])

    def test_learning_unit_creation_form_with_invalid_data(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_faulty_acronym())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['acronym'], [_('invalid_acronym')])

    def test_create_learning_unit_case_invalid_academic_year(self):
        now = datetime.datetime.now()
        bad_academic_year = AcademicYearFactory.build(year=now.year + 100)
        super(AcademicYear, bad_academic_year).save()
        data = dict(self.get_valid_data())
        data['academic_year'] = bad_academic_year.id
        form = CreateLearningUnitYearForm(person=self.person, data=data)
        self.assertFalse(form.is_valid())

    def test_learning_unit_creation_form_with_existing_acronym(self):
        LearningUnitYearFactory(acronym="LDRT2018", academic_year=self.current_academic_year)
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_existing_acronym())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['acronym'], [_('existing_acronym')])

    def test_learning_unit_creation_form_with_field_is_required_empty(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_empty_internship_subtype())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['internship_subtype'], [_('field_is_required')])

    def test_learning_unit_check_acronym(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        url = reverse('check_acronym', kwargs={'type': FULL})
        get_data = {'acronym': 'goodacronym', 'year_id': self.academic_year_1.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': False,
             'existing_acronym': False,
             'existed_acronym': False,
             'first_using': "",
             'last_using': ""}
        )

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1210', 'year_id': self.current_academic_year.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': True,
             'existed_acronym': False,
             'first_using': str(self.current_academic_year),
             'last_using': ""}
        )

        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1211",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1211', 'year_id': self.academic_year_6.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': False,
             'existed_acronym': True,
             'first_using': "",
             'last_using': str(self.current_academic_year)}
        )

    def _get_volumes_data(self, learning_units_year):
        if not isinstance(learning_units_year, list):
            learning_units_year = [learning_units_year]
        data = {}
        for learning_unit_year in learning_units_year:
            data['VOLUME_TOTAL_REQUIREMENT_ENTITIES_{}_{}'.format(learning_unit_year.id,
                                                                  self.learning_component_yr.id)] = [60]
            data['VOLUME_Q1_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [10]
            data['VOLUME_Q2_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [20]
            data['VOLUME_TOTAL_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [30]
            data['PLANNED_CLASSES_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [2]
        return data

    @staticmethod
    def _get_volumes_wrong_data(learning_unit_year, learning_component_year):
        return {
            'VOLUME_TOTAL_REQUIREMENT_ENTITIES_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [60],
            'VOLUME_Q1_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [15],
            'VOLUME_Q2_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [20],
            'VOLUME_TOTAL_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [30],
            'PLANNED_CLASSES_{}_{}'.format(learning_unit_year.id, learning_component_year.id): [2]
        }

    @mock.patch("base.models.learning_unit_year.count_search_results")
    def test_error_message_case_too_many_results_to_show(self, mock_count):
        mock_count.return_value = SearchForm.MAX_RECORDS + 1
        response = self.client.get(reverse('learning_units'), {'academic_year_id': self.academic_year_1.id})
        messages = list(response.context['messages'])
        self.assertEqual(messages[0].message, _('too_many_results'))

    def test_get_username_with_no_person(self):
        a_username = 'dupontm'
        a_user = UserFactory(username=a_username)
        self.assertEqual(base.business.learning_unit._get_name_or_username(a_user), a_username)

    def test_get_username_with_person(self):
        a_user = UserFactory(username='dupontm')
        last_name = 'dupont'
        first_name = 'marcel'
        self.person = PersonFactory(user=a_user, last_name=last_name, first_name=first_name)
        self.assertEqual(base.business.learning_unit._get_name_or_username(a_user),
                         '{}, {}'.format(last_name, first_name))

    def test_prepare_xls_content_no_data(self):
        self.assertEqual(base.business.learning_unit.prepare_xls_content([]), [])

    def test_learning_unit_year_form_with_faculty_user(self):
        faculty_managers_group = Group.objects.get(name='faculty_managers')
        faculty_user = UserFactory()
        faculty_user.groups.add(faculty_managers_group)
        faculty_person = PersonFactory(user=faculty_user)
        PersonEntityFactory(person=faculty_person, entity=self.entity)
        data = dict(self.get_valid_data())
        data['container_type'] = MASTER_THESIS
        form = CreateLearningUnitYearForm(person=faculty_person, data=data)
        self.assertTrue(form.is_valid(), form.errors)
        url = reverse('learning_unit_year_add')
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(LearningUnitYear.objects.all().count(), 7)

    def test_learning_unit_form_without_allocation_entity(self):
        faultydict = dict(self.get_valid_data())
        faultydict['allocation_entity'] = None
        form = CreateLearningUnitYearForm(person=self.person, data=faultydict)
        self.assertFalse(form.is_valid(), form.errors)
        self.assertTrue(form.errors['allocation_entity'])

    def test_expected_partim_creation_on_6_years(self):
        # Create container + container year for N+6
        a_learning_container = LearningContainerFactory()
        a_learning_container_yr_1 = self.build_learning_container_year(a_learning_container, self.current_academic_year)
        a_learning_container_yr_2 = self.build_learning_container_year(a_learning_container, self.academic_year_1)
        a_learning_container_yr_3 = self.build_learning_container_year(a_learning_container, self.academic_year_2)
        a_learning_container_yr_4 = self.build_learning_container_year(a_learning_container, self.academic_year_3)
        a_learning_container_yr_5 = self.build_learning_container_year(a_learning_container, self.academic_year_4)
        a_learning_container_yr_6 = self.build_learning_container_year(a_learning_container, self.academic_year_5)
        a_learning_container_yr_7 = self.build_learning_container_year(a_learning_container, self.academic_year_6)
        learning_container_yrs = [a_learning_container_yr_1, a_learning_container_yr_2, a_learning_container_yr_3,
                                  a_learning_container_yr_4, a_learning_container_yr_5, a_learning_container_yr_6,
                                  a_learning_container_yr_7]

        # Create UE with NO end_year
        a_learning_unit = LearningUnitFactory(end_year=None)
        learning_unit_year_parent = LearningUnitYearFactory(acronym='LBIR1200',
                                                            academic_year=self.current_academic_year,
                                                            subtype=learning_unit_year_subtypes.FULL,
                                                            learning_container_year=a_learning_container_yr_1,
                                                            learning_unit=a_learning_unit,
                                                            credits=Decimal(5.5))

        valid_partim_data = self.get_base_partim_form_data(learning_unit_year_parent)
        # Learning unit year parent doesn't have any additional entities
        del valid_partim_data['additional_requirement_entity_1']
        del valid_partim_data['additional_requirement_entity_2']

        form = CreatePartimForm(person=self.person, learning_unit_year_parent=learning_unit_year_parent,
                                data=valid_partim_data)
        self.assertTrue(form.is_valid(), form.errors)
        full_acronym = form.cleaned_data['acronym']

        url = reverse('learning_unit_year_partim_add',
                      kwargs={'learning_unit_year_id': learning_unit_year_parent.id})
        response = self.client.post(url, data=valid_partim_data)
        self.assertEqual(response.status_code, 302)

        count_learning_unit_year = LearningUnitYear.objects.filter(acronym=full_acronym).count()
        self.assertEqual(count_learning_unit_year, 7)
        count_partims = LearningUnitYear.objects.filter(subtype=learning_unit_year_subtypes.PARTIM,
                                                        learning_container_year__in=learning_container_yrs) \
            .count()
        self.assertEqual(count_partims, 7)

    def test_partim_creation_when_learning_unit_end_date_is_before_6_future_years(self):
        # Create container + container year for N+1
        a_learning_container = LearningContainerFactory()
        a_learning_container_yr_1 = self.build_learning_container_year(a_learning_container, self.current_academic_year)
        a_learning_container_yr_2 = self.build_learning_container_year(a_learning_container, self.academic_year_1)
        learning_container_yrs = [a_learning_container_yr_1,
                                  a_learning_container_yr_2]

        # Create UE with end_year set to N+1
        a_learning_unit = LearningUnitFactory(end_year=self.academic_year_1.year)
        learning_unit_year_parent = LearningUnitYearFactory(acronym='LBIR1200',
                                                            academic_year=self.current_academic_year,
                                                            subtype=learning_unit_year_subtypes.FULL,
                                                            learning_container_year=a_learning_container_yr_1,
                                                            learning_unit=a_learning_unit,
                                                            credits=Decimal(5.5))

        valid_partim_data = self.get_base_partim_form_data(learning_unit_year_parent)
        # Learning unit year parent doesn't have any additional entities
        del valid_partim_data['additional_requirement_entity_1']
        del valid_partim_data['additional_requirement_entity_2']

        form = CreatePartimForm(person=self.person, learning_unit_year_parent=learning_unit_year_parent,
                                data=valid_partim_data)
        self.assertTrue(form.is_valid(), form.errors)
        full_acronym = form.cleaned_data['acronym']

        url = reverse('learning_unit_year_partim_add',
                      kwargs={'learning_unit_year_id': learning_unit_year_parent.id})
        response = self.client.post(url, data=valid_partim_data)
        self.assertEqual(response.status_code, 302)

        count_learning_unit_year = LearningUnitYear.objects.filter(acronym=full_acronym).count()
        self.assertEqual(count_learning_unit_year, 2)
        count_learning_unit_year = LearningUnitYear.objects.filter(subtype=learning_unit_year_subtypes.PARTIM,
                                                                   learning_container_year__in=learning_container_yrs) \
            .count()
        self.assertEqual(count_learning_unit_year, 2)

    def test_partim_creation_when_credits_partim_is_equals_than_ue_parent(self):
        """The credits of partim cannot be equals to credits of UE"""
        a_learning_container_year = LearningContainerYearFactory(acronym='LBIR1200',
                                                                 academic_year=self.current_academic_year)
        learning_unit_year_parent = LearningUnitYearFactory(acronym=a_learning_container_year.acronym,
                                                            academic_year=self.current_academic_year,
                                                            subtype=learning_unit_year_subtypes.FULL,
                                                            learning_container_year=a_learning_container_year,
                                                            credits=Decimal(15))

        valid_partim_data = self.get_base_partim_form_data(learning_unit_year_parent)
        valid_partim_data['credits'] = '15'
        # Learning unit year parent doesn't have any additional entities
        del valid_partim_data['additional_requirement_entity_1']
        del valid_partim_data['additional_requirement_entity_2']

        form = CreatePartimForm(person=self.person, learning_unit_year_parent=learning_unit_year_parent,
                                data=valid_partim_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors['credits'])

    def test_partim_creation_when_credits_partim_is_greater_than_ue_parent(self):
        """The credits of partim cannot be greater than credits of UE"""
        a_learning_container_year = LearningContainerYearFactory(acronym='LBIR1200',
                                                                 academic_year=self.current_academic_year)
        learning_unit_year_parent = LearningUnitYearFactory(acronym=a_learning_container_year.acronym,
                                                            academic_year=self.current_academic_year,
                                                            subtype=learning_unit_year_subtypes.FULL,
                                                            learning_container_year=a_learning_container_year,
                                                            credits=Decimal(2))

        valid_partim_data = self.get_base_partim_form_data(learning_unit_year_parent)
        valid_partim_data['credits'] = '10'
        # Learning unit year parent doesn't have any additional entities
        del valid_partim_data['additional_requirement_entity_1']
        del valid_partim_data['additional_requirement_entity_2']

        form = CreatePartimForm(person=self.person, learning_unit_year_parent=learning_unit_year_parent,
                                data=valid_partim_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors['credits'])

    def test_get_partim_creation_form_initial_data(self):
        l_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                        acronym='LBIR1200',
                                                        container_type=learning_container_year_types.COURSE,
                                                        campus=self.campus,
                                                        language=self.language)
        l_unit = LearningUnitFactory(faculty_remark="Remarks Faculty", other_remark="Other Remarks",
                                     periodicity=learning_unit_periodicity.ANNUAL)
        learning_unit_year_parent = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                            learning_unit=l_unit,
                                                            acronym='LBIR1200',
                                                            subtype=learning_unit_year_subtypes.FULL,
                                                            learning_container_year=l_container_year,
                                                            credits=Decimal(5),
                                                            session=learning_unit_year_session.SESSION_1XX,
                                                            quadrimester=learning_unit_year_quadrimesters.Q1)
        initial = compute_partim_form_initial_data(learning_unit_year_parent)
        self.assertTrue(initial)
        self.assertIsInstance(initial, dict)
        self.assertEqual(initial['academic_year'], self.current_academic_year.id)
        self.assertEqual(initial['first_letter'], "L")
        self.assertEqual(initial['acronym'], "BIR1200")
        self.assertEqual(initial['subtype'], learning_unit_year_subtypes.PARTIM)
        self.assertEqual(initial['container_type'], learning_container_year_types.COURSE)
        self.assertTrue(initial['status'])
        self.assertEqual(initial['language'], self.language.id)
        self.assertEqual(initial['credits'], Decimal(5))
        self.assertEqual(initial['session'], learning_unit_year_session.SESSION_1XX)
        self.assertEqual(initial['faculty_remark'], "Remarks Faculty")
        self.assertEqual(initial['other_remark'], "Other Remarks")
        self.assertEqual(initial['periodicity'], learning_unit_periodicity.ANNUAL)
        self.assertEqual(initial['quadrimester'], learning_unit_year_quadrimesters.Q1)
        self.assertEqual(initial['campus'], self.campus.id)

    def test_get_partim_creation_form(self):
        luy_parent = LearningUnitYearFactory(acronym='LBIR1200',
                                             learning_container_year=self.learning_container_yr,
                                             academic_year=self.learning_container_yr.academic_year,
                                             subtype=learning_unit_year_subtypes.FULL)
        url = reverse('learning_unit_create_partim', args=[luy_parent.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/partim_form.html')
        form_initial_data = response.context['form'].initial
        #  Ensure that PARTIM is predefined value
        self.assertEqual(form_initial_data['subtype'], learning_unit_year_subtypes.PARTIM)
        self.assertEqual(form_initial_data['academic_year'], self.learning_container_yr.academic_year.id)
        self.assertEqual(form_initial_data['first_letter'], 'L')
        self.assertEqual(form_initial_data['acronym'], 'BIR1200')

    def test_get_internship_partim_creation_form(self):
        self.learning_container_yr.container_type = learning_container_year_types.INTERNSHIP
        luy_parent = LearningUnitYearFactory(acronym='LBIR1200',
                                             learning_container_year=self.learning_container_yr,
                                             academic_year=self.learning_container_yr.academic_year,
                                             subtype=learning_unit_year_subtypes.FULL,
                                             internship_subtype=internship_subtypes.CLINICAL_INTERNSHIP)
        url = reverse('learning_unit_create_partim', args=[luy_parent.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/partim_form.html')
        form_initial_data = response.context['form'].initial
        self.assertEqual(form_initial_data['internship_subtype'], internship_subtypes.CLINICAL_INTERNSHIP)

    def test_get_partim_creation_form_when_can_not_create_partim(self):
        luy_parent = LearningUnitYearFactory(subtype=learning_unit_year_subtypes.FULL)
        url = reverse('learning_unit_create_partim', args=[luy_parent.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    @mock.patch('base.views.learning_unit.PARTIM_FORM_READ_ONLY_FIELD', {'container_type', 'campus'})
    def test_get_post_data_without_read_only_field(self):
        post_data = {'other_remark': 'Autre remarque', 'container_type': learning_container_year_types.COURSE,
                     'campus': self.campus.id}
        post_data_filtered = _get_post_data_without_read_only_field(post_data)
        self.assertIsInstance(post_data_filtered, dict)
        self.assertEqual(post_data_filtered['other_remark'], 'Autre remarque')
        self.assertRaises(KeyError, lambda: post_data_filtered['container_type'])
        self.assertRaises(KeyError, lambda: post_data_filtered['campus'])

    def build_learning_container_year(self, a_learning_container, an_academic_year):
        a_learning_container_yr = LearningContainerYearFactory(academic_year=an_academic_year,
                                                               learning_container=a_learning_container,
                                                               campus=self.campus,
                                                               container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=a_learning_container_yr,
                                   entity=self.entity_version.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        EntityContainerYearFactory(learning_container_year=a_learning_container_yr,
                                   entity=self.entity_version.entity,
                                   type=entity_container_year_link_type.ALLOCATION_ENTITY)
        return a_learning_container_yr

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ])
    def test_find_inexisting_language_in_settings(self):
        wrong_language_code = 'pt'
        self.assertIsNone(learning_unit_business.find_language_in_settings(wrong_language_code))

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ])
    def test_find_language_in_settings(self):
        existing_language_code = 'en'
        self.assertEquals(learning_unit_business.find_language_in_settings(existing_language_code), ('en', 'English'))

    @mock.patch('base.views.layout.render')
    def test_learning_unit_pedagogy(self, mock_render):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr)

        request = self.create_learning_unit_request(learning_unit_year)

        from base.views.learning_unit import learning_unit_pedagogy

        learning_unit_pedagogy(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/pedagogy.html')
        self.assertIsInstance(context['form_french'], LearningUnitPedagogyForm)
        self.assertIsInstance(context['form_english'], LearningUnitPedagogyForm)

    @mock.patch('base.views.layout.render')
    def test_learning_unit_specification(self, mock_render):
        learning_unit_year = LearningUnitYearFactory()

        request = self.create_learning_unit_request(learning_unit_year)

        from base.views.learning_unit import learning_unit_specifications

        learning_unit_specifications(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/specifications.html')
        self.assertIsInstance(context['form_french'], LearningUnitSpecificationsForm)
        self.assertIsInstance(context['form_english'], LearningUnitSpecificationsForm)

    @mock.patch('base.views.layout.render')
    def test_learning_unit_attributions(self, mock_render):
        learning_unit_year = LearningUnitYearFactory()

        request = self.create_learning_unit_request(learning_unit_year)

        from base.views.learning_unit import learning_unit_attributions

        learning_unit_attributions(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/attributions.html')

    @mock.patch('base.views.layout.render')
    def test_learning_unit_specifications_edit(self, mock_render):
        a_label = 'label'
        learning_unit_year = LearningUnitYearFactory()
        text_label_lu = TextLabelFactory(order=1, label=a_label, entity=entity_name.LEARNING_UNIT_YEAR)
        TranslatedTextFactory(text_label=text_label_lu, entity=entity_name.LEARNING_UNIT_YEAR)
        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit',
                                              args=[learning_unit_year.id]), data={
            'label': a_label,
            'language': 'en'
        })
        request.user = self.a_superuser
        # request.label = 'label'
        # request.language = 'en'
        from base.views.learning_unit import learning_unit_specifications_edit

        learning_unit_specifications_edit(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/specifications_edit.html')
        self.assertIsInstance(context['form'], LearningUnitSpecificationsEditForm)

    def create_learning_unit_request(self, learning_unit_year):
        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit',
                                              args=[learning_unit_year.id]))
        request.user = self.a_superuser
        return request


class LearningUnitCreate(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.url = reverse('learning_unit_create', args=[2015])
        self.language = LanguageFactory(code='FR')

        self.client.force_login(self.person.user)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        from django.utils.encoding import uri_to_iri
        self.assertEqual(uri_to_iri(uri_to_iri(response.url)), '/login/?next={}'.format(self.url))
        self.assertEqual(response.status_code, 302)

    def test_when_user_has_not_permission(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_when_user_has_permission(self):
        content_type = ContentType.objects.get_for_model(LearningUnit)
        permission = Permission.objects.get(codename="can_create_learningunit",
                                            content_type=content_type)
        self.person.user.user_permissions.add(permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/learning_unit_form.html')

        self.assertIsInstance(response.context['form'], CreateLearningUnitYearForm)


class LearningUnitYearAdd(TestCase):
    def setUp(self):
        create_current_academic_year()
        self.person = PersonFactory()
        content_type = ContentType.objects.get_for_model(LearningUnit)
        permission = Permission.objects.get(codename="can_create_learningunit",
                                            content_type=content_type)
        self.person.user.user_permissions.add(permission)
        self.url = reverse('learning_unit_year_add')

        self.client.force_login(self.person.user)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_when_user_has_not_permission(self):
        a_person = PersonFactory()
        self.client.force_login(a_person.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_when_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTemplateUsed(response, 'method_not_allowed.html')

    def test_when_empty_form_data(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/learning_unit_form.html')

        self.assertIsInstance(response.context['form'], CreateLearningUnitYearForm)

    def test_when_valid_form_data(self):
        today = datetime.date.today()
        academic_year_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                    end_date=today.replace(year=today.year + 2),
                                                    year=today.year + 1)
        academic_year_2 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 2),
                                                    end_date=today.replace(year=today.year + 3),
                                                    year=today.year + 2)
        academic_year_3 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 3),
                                                    end_date=today.replace(year=today.year + 4),
                                                    year=today.year + 3)
        academic_year_4 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 4),
                                                    end_date=today.replace(year=today.year + 5),
                                                    year=today.year + 4)
        academic_year_5 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 5),
                                                    end_date=today.replace(year=today.year + 6),
                                                    year=today.year + 5)
        academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                    end_date=today.replace(year=today.year + 7),
                                                    year=today.year + 6)
        current_academic_year = AcademicYearFactory(start_date=today,
                                                    end_date=today.replace(year=today.year + 1),
                                                    year=today.year)
        super(AcademicYear, academic_year_1).save()
        super(AcademicYear, academic_year_2).save()
        super(AcademicYear, academic_year_3).save()
        super(AcademicYear, academic_year_4).save()
        super(AcademicYear, academic_year_5).save()
        super(AcademicYear, academic_year_6).save()

        organization = OrganizationFactory(type=organization_type.MAIN)
        campus = CampusFactory(organization=organization)
        entity = EntityFactory(organization=organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, start_date=today,
                                              end_date=today.replace(year=today.year + 1))
        language = LanguageFactory()

        form_data = {
            "first_letter": "L",
            "acronym": "TAU2000",
            "container_type": learning_container_year_types.COURSE,
            "academic_year": current_academic_year.id,
            "status": True,
            "periodicity": learning_unit_periodicity.ANNUAL,
            "credits": "5",
            "campus": campus.id,
            "internship_subtype": internship_subtypes.TEACHING_INTERNSHIP,
            "title": "LAW",
            "title_english": "LAW",
            "requirement_entity": entity_version.id,
            "subtype": learning_unit_year_subtypes.FULL,
            "language": language.id,
            "session": learning_unit_year_session.SESSION_P23,
            "faculty_remark": "faculty remark",
            "other_remark": "other remark"
        }

        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)


class TestCreateXls(TestCase):
    def setUp(self):
        self.learning_unit_year = LearningUnitYearFactory(learning_container_year=LearningContainerYearFactory(),
                                                          acronym="LOSI1452")
        self.requirement_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        self.allocation_entity_container = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.ALLOCATION_ENTITY)

        self.user = UserFactory()

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_no_data(self, mock_generate_xls):
        learning_unit_business.create_xls(self.user, [])
        expected_argument = _generate_xls_build_parameter([], self.user)
        mock_generate_xls.assert_called_with(expected_argument)

    @mock.patch("osis_common.document.xls_build.generate_xls")
    def test_generate_xls_data_with_a_learning_unit(self, mock_generate_xls):
        a_form = LearningUnitYearForm({"acronym": self.learning_unit_year.acronym}, service_course_search=False)
        self.assertTrue(a_form.is_valid())
        found_learning_units = a_form.get_activity_learning_units()
        learning_unit_business.create_xls(self.user, found_learning_units)
        xls_data = [[self.learning_unit_year.academic_year.name, self.learning_unit_year.acronym,
                     self.learning_unit_year.specific_title,
                     xls_build.translate(self.learning_unit_year.learning_container_year.container_type),
                     xls_build.translate(self.learning_unit_year.subtype), None, None, self.learning_unit_year.credits,
                     xls_build.translate(self.learning_unit_year.status)]]
        expected_argument = _generate_xls_build_parameter(xls_data, self.user)
        mock_generate_xls.assert_called_with(expected_argument)


def _generate_xls_build_parameter(xls_data, user):
    return {
        xls_build.LIST_DESCRIPTION_KEY: "Liste d'activités",
        xls_build.FILENAME_KEY: 'Learning_units',
        xls_build.USER_KEY: user.username,
        xls_build.WORKSHEETS_DATA: [{
            xls_build.CONTENT_KEY: xls_data,
            xls_build.HEADER_TITLES_KEY: [str(_('academic_year_small')),
                                          str(_('code')),
                                          str(_('title')),
                                          str(_('type')),
                                          str(_('subtype')),
                                          str(_('requirement_entity_small')),
                                          str(_('allocation_entity_small')),
                                          str(_('credits')),
                                          str(_('active_title'))],
            xls_build.WORKSHEET_TITLE_KEY: 'Learning_units',
        }]
    }


class TestLearningUnitComponents(TestCase):
    def setUp(self):
        self.academic_years = GenerateAcademicYear(start_year=2010, end_year=2020).academic_years
        self.generated_container = GenerateContainer(start_year=2010, end_year=2020)
        self.a_superuser = SuperUserFactory()
        self.person = PersonFactory(user=self.a_superuser)

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_components(self, mock_program_manager, mock_render):

        mock_program_manager.return_value = True

        learning_unit_year = self.generated_container.generated_container_years[0].learning_unit_year_full

        request_factory = RequestFactory()
        request = request_factory.get(reverse(learning_unit_components, args=[learning_unit_year.id]))
        request.user = self.a_superuser

        learning_unit_components(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/components.html')
        components = context['components']
        self.assertEqual(len(components), 4)

        for component in components:
            self.assertIn(component['learning_component_year'],
                          self.generated_container.generated_container_years[0].list_components)

            volumes = component['volumes']
            self.assertEqual(volumes['VOLUME_Q1'], None)
            self.assertEqual(volumes['VOLUME_Q2'], None)


class TestLearningUnitProposalDisplay(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language_pt = LanguageFactory(code='PT')
        cls.language_it = LanguageFactory(code='IT')
        cls.campus = CampusFactory()
        cls.academic_year = create_current_academic_year()
        cls.l_container_year = LearningContainerYearFactory(acronym="LBIR1212",
                                                            academic_year=cls.academic_year,
                                                            language=cls.language_pt,
                                                            campus=cls.campus)
        cls.learning_unit = LearningUnitFactory(learning_container=cls.l_container_year.learning_container)
        cls.learning_unit_yr = LearningUnitYearFactory(acronym="LBIR1212",
                                                       learning_unit=cls.learning_unit,
                                                       learning_container_year=cls.l_container_year,
                                                       academic_year=cls.academic_year,
                                                       subtype=learning_unit_year_subtypes.FULL,
                                                       status=True,
                                                       quadrimester="Q3",
                                                       credits=4)

        cls.proposal_learning_unit = ProposalLearningUnitFactory(learning_unit_year=cls.learning_unit_yr)
        cls.initial_credits = 3.0
        cls.initial_quadrimester = 'Q1'
        cls.initial_language = cls.language_it.id
        cls.initial_data_learning_unit_year = {'credits': cls.initial_credits,
                                               'quadrimester': cls.initial_quadrimester}

        cls.intitial_language_en = cls.language_it

    def test_is_foreign_key(self):
        actual_data = {"language{}".format(END_FOREIGN_KEY_NAME): self.language_it.id}
        self.assertTrue(_is_foreign_key("language", actual_data))

    def test_is_not_foreign_key(self):
        actual_data = {"credits": self.language_it.id}
        self.assertFalse(_is_foreign_key("credits", actual_data))

    def test_check_differences(self):
        initial_data_learning_unit_year = {'credits': self.initial_credits,
                                           'quadrimester': self.initial_quadrimester}
        actual_data = {"credits": self.learning_unit_yr.credits, 'quadrimester': 'Q3'}

        differences = _check_differences(initial_data_learning_unit_year, actual_data)

        self.assertEqual(differences.get('credits'),
                         "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL, self.initial_credits))
        self.assertEqual(differences.get('quadrimester'),
                         "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL, self.initial_quadrimester))

    def test_get_the_old_value(self):
        differences = _get_the_old_value('credits',
                                         {"credits": self.initial_credits + 1},
                                         {'credits': self.initial_credits})
        self.assertEqual(differences.get('credits'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                      self.initial_credits))
    def test_get_the_old_value_no_initial_value(self):
        differences = _get_the_old_value('credits',
                                         {"credits": self.initial_credits + 1},
                                         {})
        self.assertEqual(differences.get('credits'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                      NO_PREVIOUS_VALUE))

    def test_get_the_old_value_for_foreign_key(self):
        initial_data_learning_container_year = {'language': self.language_pt.id}
        actual_data = {"language_id": self.language_it.id}
        differences = _get_the_old_value('language', actual_data, initial_data_learning_container_year)
        self.assertEqual(differences.get('language'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL, self.language_pt))

    def test_get_the_old_value_for_foreign_key_no_previous_value(self):
        initial_data = {"language": None}
        actual_data = {"language_id": self.language_it.id}

        differences = _get_the_old_value('language', actual_data, initial_data)
        self.assertEqual(differences.get('language'), "{} : -".format(LABEL_VALUE_BEFORE_PROPROSAL))

        initial_data = {}
        differences = _get_the_old_value('language', actual_data, initial_data)
        self.assertEqual(differences.get('language'), "{} : -".format(LABEL_VALUE_BEFORE_PROPROSAL))

    def test_get_the_old_value_with_translation(self):
        cle = VALUES_WHICH_NEED_TRANSLATION[0]
        initial_data = {cle: learning_unit_periodicity.ANNUAL}
        actual_data = {cle: learning_unit_periodicity.BIENNIAL_EVEN}
        differences = _get_the_old_value(cle, actual_data, initial_data)
        self.assertEqual(differences.get(cle), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                _(learning_unit_periodicity.ANNUAL)))

    def test_compare_model_with_initial_value(self):
        differences = _compare_model_with_initial_value(self.proposal_learning_unit.learning_unit_year.id,
                                                        {"credits": self.initial_credits,
                                                         'quadrimester': self.initial_quadrimester},
                                                        apps.get_model(app_label='base', model_name="LearningUnitYear"))
        self.assertEqual(differences.get('credits'),
                         "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,  self.initial_credits))

    def test_compare_model_with_initial_value_not_found_id(self):
        differences = _compare_model_with_initial_value(-1,
                                                        None,
                                                        apps.get_model(app_label='base', model_name="LearningUnitYear"))
        self.assertEqual(differences, {})

    def test_get_str_representing_old_data_from_foreign_key(self):
        differences = _get_str_representing_old_data_from_foreign_key('campus', self.campus.id)
        self.assertEqual(differences.get('campus'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,  self.campus))

    def test_get_str_representing_old_data_from_foreign_key_equals_no_value(self):
        differences = _get_str_representing_old_data_from_foreign_key('campus', NO_PREVIOUS_VALUE)
        self.assertEqual(differences.get('campus'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL, NO_PREVIOUS_VALUE))

    def test_replace_key_of_foreign_key(self):
        changed_dict = _replace_key_of_foreign_key({'key1{}'.format(END_FOREIGN_KEY_NAME): 1, 'key2': 2})
        self.assertEqual(changed_dict, {'key1': 1, 'key2': 2})

    def test_check_differences_none(self):
        self.assertEqual(_check_differences({}, {}), {})
        self.assertEqual(_check_differences(None, {}), {})
        self.assertEqual(_check_differences({'key1': 1, 'key2': 2}, {'key1': 1, 'key2': 2}), {})
        self.assertEqual(_check_differences({'key1': 1, 'key2': 2}, {'key1_id': 1, 'key2': 2}), {})

    def test_check_differences(self):
        self.assertEqual(len(_check_differences({'key1': 1, 'key2': 2}, {'key1_id': 1, 'key2': 9999999999999})), 1)
        result = _check_differences({'key1': 1, 'key2': 'new_value'}, {'key1': 1, 'key2': 'old_value'})
        self.assertEqual(result.get('key2'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,  'new_value'))

    def test_get_difference_of_proposal(self):
        self.assertEqual(_get_difference_of_proposal(None), {})

    def test_get_old_value_of_foreign_key_for_campus(self):
        differences = _get_old_value_of_foreign_key('campus', self.campus.id)
        self.assertEqual(differences.get('campus'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                     self.campus))

    def test_get_old_value_of_foreign_key_for_language(self):
        differences = _get_old_value_of_foreign_key('language', self.language_it.id)
        self.assertEqual(differences.get('language'), "{} : {}".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                       self.language_it))

    def test_has_changed_entity(self):
        an_entity = EntityFactory()
        an_entity_container_year = EntityContainerYearFactory(entity=an_entity)

        an_other_entity = EntityFactory()

        self.assertTrue(_has_changed_entity(an_entity_container_year, an_other_entity.id ))
        self.assertFalse(_has_changed_entity(an_entity_container_year, an_entity.id ))



