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
from reference.tests.factories.country import CountryFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


def create_entities_hierarchy(self):
    country = CountryFactory()
    # Root entity
    self.root_entity = EntityFactory(country=country)
    self.root_entity_version = EntityVersionFactory(entity=self.root_entity, acronym="ROOT_V", parent=None,
                                                    end_date=None)

    # Child 1 entity to root
    self.child_one_entity = EntityFactory(country=country)
    self.child_one_entity_version = EntityVersionFactory(acronym="CHILD_1_V", parent=self.root_entity,
                                                         end_date=None, entity=self.child_one_entity)

    # Child 2 entity to root
    self.child_two_entity = EntityFactory(country=country)
    self.child_two_entity_version = EntityVersionFactory(acronym="CHILD_2_V", parent=self.root_entity,
                                                         end_date=None, entity=self.child_two_entity)

