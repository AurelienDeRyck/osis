##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from base.tests.models import test_person
from base.models import program_manager
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.academic_year import AcademicYearFactory
from django.test import TestCase

def create_program_manager(offer_year, person=None):
    if not person:
        person = PersonFactory(first_name="program", last_name="manager")
    return ProgramManagerFactory(offer_year=offer_year, person=person)

class FindByOfferYearTest(TestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory(year=datetime.datetime.now().year)
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)

    def test_case_offer_is_none(self):
        self.assertEquals(len(program_manager.find_by_offer_year(None)), 0)

    def test_case_no_existing_program_manager_for_one_offer(self):
        offer_year = OfferYearFactory(academic_year=self.academic_year)
        self.assertEquals(len(program_manager.find_by_offer_year(offer_year)), 0)

    def test_case_with_existing_program_manager(self):
        ProgramManagerFactory(offer_year=self.offer_year)
        self.assertEquals(len(program_manager.find_by_offer_year(self.offer_year)), 1)

    def test_return_sorted_managers(self):
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Yannick", last_name="Leblanc"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Yannick", last_name="Ferreira"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Laura", last_name="Ferreira"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Bob", last_name="Uncle"))
        ProgramManagerFactory(offer_year=self.offer_year, person=PersonFactory(first_name="Laura", last_name="Dupont"))

        managers = program_manager.find_by_offer_year(self.offer_year)
        self.assertEquals(managers[0].person.last_name, "Dupont")
        self.assertEquals(managers[1].person.last_name, "Ferreira")
        self.assertEquals(managers[1].person.first_name, "Laura")
        self.assertEquals(managers[2].person.last_name, "Ferreira")
        self.assertEquals(managers[2].person.first_name, "Yannick")
        self.assertEquals(managers[3].person.last_name, "Leblanc")
        self.assertEquals(managers[4].person.last_name, "Uncle")

    def test_is_program_manager(self):
        user = UserFactory(username="PGRM_1")
        ProgramManagerFactory(offer_year=self.offer_year, person= PersonFactory(user=user))
        self.assertTrue(program_manager.is_program_manager(user=user))

    def test_is_not_program_manager(self):
        user = UserFactory(username="NO_PGRM")
        self.assertFalse(program_manager.is_program_manager(user=user))