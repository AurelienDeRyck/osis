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

from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from base.business.learning_units import perms
from base.models.academic_year import AcademicYear
from base.models.enums import entity_container_year_link_type
from base.models.enums import proposal_state, proposal_type, learning_container_year_types
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.person import FACULTY_MANAGER_GROUP, CENTRAL_MANAGER_GROUP
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.learning_unit import LearningUnitFactory

TYPES_PROPOSAL_NEEDED_TO_EDIT = (learning_container_year_types.COURSE,
                                 learning_container_year_types.DISSERTATION,
                                 learning_container_year_types.INTERNSHIP)

TYPES_DIRECT_EDIT_PERMITTED = (learning_container_year_types.OTHER_COLLECTIVE,
                               learning_container_year_types.OTHER_INDIVIDUAL,
                               learning_container_year_types.MASTER_THESIS,
                               learning_container_year_types.EXTERNAL)

ALL_TYPES = TYPES_PROPOSAL_NEEDED_TO_EDIT + TYPES_DIRECT_EDIT_PERMITTED


class PermsTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_yr = AcademicYearFactory(start_date=today,
                                               end_date=today.replace(year=today.year + 1),
                                               year=today.year)
        self.academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                         end_date=today.replace(year=today.year + 7),
                                                         year=today.year + 6)
        super(AcademicYear, self.academic_year_6).save()

    def test_can_faculty_manager_modify_end_date_partim(self):
        for container_type in ALL_TYPES:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=PARTIM)

            self.assertTrue(luy.can_update_by_faculty_manager())

    def test_can_faculty_manager_modify_end_date_full(self):
        for direct_edit_permitted_container_type in TYPES_DIRECT_EDIT_PERMITTED:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=direct_edit_permitted_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertTrue(luy.can_update_by_faculty_manager())

    def test_cannot_faculty_manager_modify_end_date_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification_end_date(luy, self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP)))

    def test_cannot_faculty_manager_modify_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_year_6,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_year_6,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification(luy, self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP)))

    def test_cannot_faculty_manager_modify_end_date_no_container(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                      learning_container_year=None)
        self.assertFalse(luy.can_update_by_faculty_manager())


    def test_can_central_manager_modify_end_date_full(self):
        for proposal_needed_container_type in ALL_TYPES:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=proposal_needed_container_type)
            lu = LearningUnitFactory(end_year=self.academic_yr.year)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL,
                                          learning_unit=lu)

            self.assertTrue(
                perms.is_eligible_for_modification_end_date(
                    luy,
                    self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP)))


    def test_access_edit_learning_unit_proposal_as_central_manager(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        a_person = self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP)

        self.assertFalse(perms.is_eligible_to_edit_proposal(None, a_person))

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_access_edit_learning_unit_proposal_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP)

        self.assertFalse(perms.is_eligible_to_edit_proposal(None, a_person))

        a_proposal = ProposalLearningUnitFactory(state=proposal_state.ProposalState.CENTRAL.name,
                                                 type=proposal_type.ProposalType.SUPPRESSION.name,
                                                 learning_unit_year=luy)

        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        a_proposal.state = proposal_state.ProposalState.FACULTY.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        PersonEntityFactory(entity=an_requirement_entity, person=a_person)
        for a_type in perms.PROPOSAL_TYPE_ACCEPTED_FOR_UPDATE:
            a_proposal.type = a_type
            a_proposal.save()
            self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_is_not_eligible_for_cancel_of_proposal(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        an_entity_container_year = EntityContainerYearFactory(
            learning_container_year=luy.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )
        a_person = self.create_person_with_permission_and_group()
        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_entity_container_year.entity.id,
                }
            })
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))
        a_proposal.state = proposal_state.ProposalState.FACULTY.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))
        a_proposal.type = proposal_type.ProposalType.MODIFICATION.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_for_creation(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy,
                                                 type=proposal_type.ProposalType.CREATION.name,
                                                 state=proposal_state.ProposalState.FACULTY.name)

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_wrong_state(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_as_central_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    @staticmethod
    def create_person_with_permission_and_group(group_name=None, permission_name='can_edit_learning_unit_proposal'):
        a_user = UserFactory()
        permission, created = Permission.objects.get_or_create(
            codename=permission_name, content_type=ContentType.objects.get_for_model(ProposalLearningUnit))
        a_user.user_permissions.add(permission)
        a_person = PersonFactory(user=a_user)
        if group_name:
            a_person.user.groups.add(Group.objects.get(name=group_name))
        return a_person
