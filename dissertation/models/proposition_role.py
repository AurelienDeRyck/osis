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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PropositionRole(models.Model):
    STATUS_CHOICES = (
        ('PROMOTEUR', _('pro')),
        ('CO_PROMOTEUR', _('copro')),
        ('READER', _('reader')),
    )

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="PROMOTEUR")
    adviser = models.ForeignKey('Adviser')
    proposition_dissertation = models.ForeignKey('PropositionDissertation')

    def __str__(self):
        return u"%s %s" % (self.status if self.status else "",
                           self.adviser if self.adviser else "")


def count_proposition_roles_by_dissertation(dissertation):
    return PropositionRole.objects.filter(proposition_dissertation=dissertation.proposition_dissertation).count()
