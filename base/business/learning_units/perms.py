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
from base.models.entity import Entity
from base.models.enums import learning_container_year_types
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.person_entity import is_attached_entities

FACULTY_UPDATABLE_CONTAINER_TYPES = (learning_container_year_types.COURSE,
                                     learning_container_year_types.DISSERTATION,
                                     learning_container_year_types.INTERNSHIP)
PROPOSAL_TYPE_ACCEPTED_FOR_UPDATE = (ProposalType.CREATION.name,
                                     ProposalType.MODIFICATION.name,
                                     ProposalType.TRANSFORMATION.name,
                                     ProposalType.TRANSFORMATION_AND_MODIFICATION.name,
                                     ProposalType.SUPPRESSION.name)


def is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person):
    entity = Entity.objects.filter(
        entitycontaineryear__learning_container_year=learning_unit_year.learning_container_year,
        entitycontaineryear__type=REQUIREMENT_ENTITY)

    return is_attached_entities(person, entity)


def is_eligible_to_create_modification_proposal(learning_unit_year, person):
    if learning_unit_year.is_past() or learning_unit_year.is_partim():
        return False
    if learning_unit_year.learning_container_year and \
            learning_unit_year.learning_container_year.container_type not in FACULTY_UPDATABLE_CONTAINER_TYPES:
        return False
    if learning_unit_year.is_in_proposal():
        return False

    return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def is_eligible_for_cancel_of_proposal(proposal, person):
    if not proposal or not person.is_faculty_manager() or proposal.state != ProposalState.FACULTY.name:
        return False

    if _is_attached_to_initial_entity(proposal, person):
        return True

    return person.is_linked_to_entity_in_charge_of_learning_unit_year(proposal.learning_unit_year)


def _is_attached_to_initial_entity(learning_unit_proposal, a_person):
    if not learning_unit_proposal.initial_data.get("entities") or \
            not learning_unit_proposal.initial_data["entities"].get(REQUIREMENT_ENTITY):
        return False
    initial_entity_requirement_id = learning_unit_proposal.initial_data["entities"][REQUIREMENT_ENTITY]
    return is_attached_entities(a_person, Entity.objects.filter(pk=initial_entity_requirement_id))


def is_eligible_to_edit_proposal(proposal, person):
    if not proposal:
        return False

    is_person_linked_to_entity = person.is_linked_to_entity_in_charge_of_learning_unit_year(
        proposal.learning_unit_year)

    if person.is_faculty_manager():
        if (proposal.state != ProposalState.FACULTY.name or
                proposal.type not in PROPOSAL_TYPE_ACCEPTED_FOR_UPDATE or
                not is_person_linked_to_entity):
            return False

    return person.user.has_perm('base.can_edit_learning_unit_proposal')


def is_eligible_for_modification_end_date(learning_unit_year, person):
    if learning_unit_year.learning_unit.is_past():
        return False
    if not is_eligible_for_modification(learning_unit_year, person):
        return False
    container_type = learning_unit_year.learning_container_year.container_type
    return container_type not in FACULTY_UPDATABLE_CONTAINER_TYPES or learning_unit_year.is_partim()


def is_eligible_for_modification(learning_unit_year, person):
    if learning_unit_year.is_past():
        return False
    if learning_unit_year.is_in_proposal():
        return False
    if person.is_faculty_manager() and not learning_unit_year.can_update_by_faculty_manager():
        return False
    return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def can_delete_learning_unit_year(learning_unit_year, person):
    if not _can_delete_learning_unit_year_according_type(learning_unit_year, person):
        return False
    return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def _can_delete_learning_unit_year_according_type(learning_unit_year, person):
    if not person.is_central_manager() and person.is_faculty_manager():
        container_type = learning_unit_year.learning_container_year.container_type

        return not (
                container_type == learning_container_year_types.COURSE and learning_unit_year.is_full()
        ) and container_type not in [learning_container_year_types.DISSERTATION,
                                     learning_container_year_types.INTERNSHIP]
    return True


def learning_unit_year_permissions(learning_unit_year, person):
    return {
        'can_propose': is_eligible_to_create_modification_proposal(learning_unit_year, person),
        'can_edit_date': is_eligible_for_modification_end_date(learning_unit_year, person),
        'can_edit': is_eligible_for_modification(learning_unit_year, person),
        'can_delete': can_delete_learning_unit_year(learning_unit_year, person)
    }


def learning_unit_proposal_permissions(proposal, person):
    return {
        'can_cancel_proposal': is_eligible_for_cancel_of_proposal(proposal, person),
        'can_edit_learning_unit_proposal': is_eligible_to_edit_proposal(proposal, person)
    }
