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
from django.utils import timezone
from datetime import datetime
from base.models.entity_version import find_latest_version_by_entity
from base.models.entity_calendar import find_by_reference_and_start_date,find_by_reference_and_entity
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from attribution.models.attribution import filter_summary_responsible
from base.views.common import home
from base.models.entity import Entity
from base.utils.send_mail import send_mail_for_educational_information_update_period_opening
from base.models.person import Person, find_by_id
from base.models.academic_calendar import AcademicCalendar, get_by_reference_and_academic_year
from base.models.academic_year import current_academic_year
from base.models.enums.organization_type import MAIN


LEARNING_UNIT_YEARS = 'learning_unit_years'
PERSON = 'person'


def get_responsible_and_learning_unit_yr_list(learning_units_found):
    responsible_and_learning_unit_yr_list = []
    for learning_unit_yr in learning_units_found:
        if not learning_unit_yr.summary_status:
            responsible_and_learning_unit_yr_list = \
                _update_responsible_and_learning_unit_yr_list(learning_unit_yr, responsible_and_learning_unit_yr_list)
    return responsible_and_learning_unit_yr_list


def _update_responsible_data_with_new_learning_unit_yr(a_responsible_person, learning_unit_yr,
                                                       responsible_and_learning_unit_yr_list_param):
    responsible_and_learning_unit_yr_list = responsible_and_learning_unit_yr_list_param
    for a_known_responsible in responsible_and_learning_unit_yr_list:
        if a_known_responsible.get(PERSON) == a_responsible_person:
            learning_unit_yr_list_for_responsible = a_known_responsible.get(LEARNING_UNIT_YEARS)
            learning_unit_yr_list_for_responsible.append(learning_unit_yr)
            a_known_responsible[LEARNING_UNIT_YEARS] = learning_unit_yr_list_for_responsible
            return responsible_and_learning_unit_yr_list
    return responsible_and_learning_unit_yr_list


def _build_new_responsible_data(a_responsible_person, learning_unit_yr):
    return {PERSON: a_responsible_person,
            LEARNING_UNIT_YEARS: [learning_unit_yr]}


def _update_responsible_and_learning_unit_yr_list(learning_unit_yr, responsible_and_learning_unit_yr_list_param):
    responsible_and_learning_unit_yr_list = responsible_and_learning_unit_yr_list_param
    for responsible in learning_unit_yr.summary_responsibles:
        a_responsible_person = responsible.tutor.person
        if _is_new_responsible(responsible_and_learning_unit_yr_list, a_responsible_person):
            responsible_and_learning_unit_yr_list.append(
                _build_new_responsible_data(a_responsible_person, learning_unit_yr))
        else:
            responsible_and_learning_unit_yr_list = _update_responsible_data_with_new_learning_unit_yr(
                a_responsible_person, learning_unit_yr,
                responsible_and_learning_unit_yr_list)
    return responsible_and_learning_unit_yr_list


def _is_new_responsible(responsible_and_learning_unit_yr_list, a_person):
    for record_responsible_learning_units in responsible_and_learning_unit_yr_list:
        if record_responsible_learning_units.get(PERSON) == a_person:
            return False
    return True


def _teacher_mailing_for_summary_opened(request):
    ids=[3103]
    entities = Entity.objects.filter(organization__type=MAIN, id__in=ids)
    now_date = timezone.now().date()

    summary_responsible = get_list_of_summary_responsibles_with_entities(entities, now_date)
    print(summary_responsible)
    send_mail_for_educational_information_update_period_opening(summary_responsible)

    return home(request)


def get_list_of_summary_responsibles_with_entities(entities, now_date):
    summary_responsible = {}
    for an_entity in entities:
        opened_now = _is_updating_period_opening_today(an_entity, now_date)
        if opened_now:
            summary_responsible = get_summary_responsible_list(an_entity, summary_responsible)
    return summary_responsible


def get_summary_responsible_list(an_entity, summary_responsible_param):
    summary_responsible = summary_responsible_param.copy()
    summary_responsible_attributions = filter_summary_responsible([an_entity], True)

    if summary_responsible_attributions:
        for attribution in summary_responsible_attributions:
            id_person = attribution.tutor.person
            # id_person = attribution.get('tutor__person')
            if id_person not in summary_responsible:
                print('if')
                summary_responsible.update({id_person: [an_entity]})
            else:
                print('else')

                entities_list = summary_responsible.get(id_person)
                entities_list.append(an_entity)
                summary_responsible.update({id_person: entities_list})
    return summary_responsible


def _is_updating_period_opening_today(an_entity, now_date):
    entity_calendar = find_by_reference_and_entity(SUMMARY_COURSE_SUBMISSION,
                                                   an_entity)
    if entity_calendar:
        return True if entity_calendar.start_date.date() == now_date else False
    else:
        opened_now = find_parent_calendar(an_entity, now_date)
    return opened_now


def find_parent_calendar(an_entity, now_date):
    an_entity_version = find_latest_version_by_entity(an_entity, now_date)
    if an_entity_version:
        if an_entity_version.parent:
            entity_calendar = find_by_reference_and_entity(SUMMARY_COURSE_SUBMISSION,
                                                                          an_entity_version.parent)
            if entity_calendar:
                return True if entity_calendar.start_date.date() == now_date else False
            else:
                ev_papy = find_latest_version_by_entity(an_entity_version.parent, now_date)
                return find_parent_calendar(ev_papy.entity, now_date) if ev_papy else get_default_calendar(now_date)
        else:
            return get_default_calendar(now_date)


def get_default_calendar(now_date):
    current_academic_yr = current_academic_year()
    ac_cal = get_by_reference_and_academic_year(SUMMARY_COURSE_SUBMISSION, current_academic_yr)
    return True if ac_cal and ac_cal.start_date == now_date else False


def send_mails(ent, summary_responsible_attributions):
    send_mail_for_educational_information_update_period_opening(summary_responsible_attributions, ent)
