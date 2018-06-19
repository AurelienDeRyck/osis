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
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.forms.education_group.create import CreateEducationGroupYearForm, CreateOfferYearEntityForm
from base.models.education_group_year import EducationGroupYear
from base.models.person import Person
from base.views import layout
from base.views.common import display_success_messages


@login_required
@permission_required('base.add_educationgroup', raise_exception=True)
def create_education_group(request, parent_id=None):
    person = get_object_or_404(Person, user=request.user)
    parent = get_object_or_404(EducationGroupYear, id=parent_id) if parent_id is not None else None

    form_education_group_year = CreateEducationGroupYearForm(request.POST or None)
    form_offer_year_entity = CreateOfferYearEntityForm(request.POST or None)

    if form_offer_year_entity.is_valid() and form_education_group_year.is_valid():
        education_group_year = form_education_group_year.save(parent)
        form_offer_year_entity.save(education_group_year)

        success_msg = create_success_message_for_creation_education_group_year(education_group_year)
        display_success_messages(request, success_msg, extra_tags='safe')
        return redirect("education_group_read", education_group_year.id)

    return layout.render(request, "education_group/creation.html", locals())


def create_success_message_for_creation_education_group_year(education_group_year):
    MSG_KEY = "Education group year <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfuly created."
    link = reverse("education_group_read", args=[education_group_year.id])
    return _(MSG_KEY) % {"link": link, "acronym": education_group_year.acronym,
                         "academic_year": education_group_year.academic_year}
