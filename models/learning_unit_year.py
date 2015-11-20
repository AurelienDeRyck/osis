# -*- coding: utf-8 -*-
##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    A copy of this license - GNU Affero General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api

class Learning_unit_year(models.Model):
    _name = 'osis.learning_unit_year'
    _description = "Learning unit year"

    academic_year_id = fields.Many2one('osis.academic_year', string='Academic year')
    learning_unit_id = fields.Many2one('osis.learning_unit', string='Learning unit')
    attribution_entity_id = fields.Many2one('osis.structure', string='Attribution entity')
    specifications_responsible_id = fields.Many2one('osis.structure', string='Specifications responsible entity')

    credits = fields.Float("Credits", default=0)

    def name_get(self,cr,uid,ids,context=None):
        result={}
        for record in self.browse(cr,uid,ids,context=context):
            name_build = ''
            if record.academic_year_id.year:
                name_build += str(record.academic_year_id.year)
            if record.learning_unit_id.title:
                if record.academic_year_id.year:
                    name_build += ' - '
                name_build += record.learning_unit_id.title
            result[record.id]  = name_build
        return result.items()
