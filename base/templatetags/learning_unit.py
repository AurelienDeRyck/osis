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
from django import template
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
register = template.Library()


@register.filter
def academic_years(start_year, end_year):
    if start_year and end_year:
        str_start_year = ''
        str_end_year = ''
        if start_year:
            str_start_year = "{} {}-{}".format(_('from').title(), start_year, str(start_year+1)[-2:])
        if end_year:
            str_end_year = "{} {}-{}".format(_('to'), end_year, str(end_year+1)[-2:])
        return "{} {}".format(str_start_year, str_end_year)
    else:
        if start_year and not end_year:
            return "{} {}-{} ({})".format(_('from'), start_year, str(start_year+1)[-2:], _('not_end_year'))
        else:
            return "-"


@register.filter
def academic_year(year):
    if year:
        return "{}-{}".format(year, str(year+1)[-2:])
    return "-"


@register.filter
def get_difference_css(differences, parameter):
    if differences.get(parameter, None):
        return mark_safe(" data-toggle=tooltip title='{} : {}' class={} ".format(_("value_before_proposal"),
                                                                       differences.get(parameter),
                                                                       "proposal_value"))
    return None
