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
from django.conf.urls import url, include

from base.views import education_group
from base.views.education_groups.group_element_year.read import pdf_content
from base.views.education_groups.select import education_group_select, learning_unit_select
from . import search, create, detail, update, delete, group_element_year

urlpatterns = [

    url(r'^$', search.education_groups, name='education_groups'),
    url(r'^select_lu/(?P<learning_unit_year_id>[0-9]+)$', learning_unit_select, name='learning_unit_select'),

    url(
        r'^new/(?P<category>[A-Z_]+)/(?P<education_group_type_pk>[0-9]+)/$',
        create.create_education_group,
        name='new_education_group'
    ),
    url(
        r'^new/(?P<category>[A-Z_]+)/(?P<education_group_type_pk>[0-9]+)/(?P<parent_id>[0-9]+)/$',
        create.create_education_group,
        name='new_education_group'
    ),

    url(
        r'^select_type/(?P<category>[A-Z_]+)/$',
        create.SelectEducationGroupTypeView.as_view(),
        name='select_education_group_type'
    ),
    url(
        r'^select_type/(?P<category>[A-Z_]+)/(?P<parent_id>[0-9]+)/$',
        create.SelectEducationGroupTypeView.as_view(),
        name='select_education_group_type'
    ),
    url(r'^proxy_management/$', group_element_year.update.proxy_management, name='proxy_management'),

    url(r'^(?P<root_id>[0-9]+)/(?P<education_group_year_id>[0-9]+)/', include([

        url(r'^identification/$', detail.EducationGroupRead.as_view(), name='education_group_read'),
        url(r'^update/$', update.update_education_group, name="update_education_group"),

        url(r'^diplomas/$', detail.EducationGroupDiplomas.as_view(),
            name='education_group_diplomas'),
        url(r'^informations/$', detail.EducationGroupGeneralInformation.as_view(),
            name='education_group_general_informations'),
        url(r'^informations/edit/$', education_group.education_group_year_pedagogy_edit,
            name="education_group_pedagogy_edit"),

        url(r'^informations/remove$', education_group.education_group_year_pedagogy_remove_term,
            name="education_group_pedagogy_remove_term"),
        url(r'^informations/add$', education_group.education_group_year_pedagogy_add_term,
            name="education_group_pedagogy_add_term"),
        url(r'^informations/get_terms/(?P<language>[a-z\-]+)',
            education_group.education_group_year_pedagogy_get_terms,
            name="education_group_pedagogy_get_terms"),

        url(r'^administrative/', include([
            url(u'^$', detail.EducationGroupAdministrativeData.as_view(), name='education_group_administrative'),
            url(u'^edit/$', education_group.education_group_edit_administrative_data,
                name='education_group_edit_administrative')
        ])),
        url(r'^select/$', education_group_select, name='education_group_select'),
        url(r'^content/', include([
            url(u'^$', detail.EducationGroupContent.as_view(), name='education_group_content'),
            url(r'^(?P<group_element_year_id>[0-9]+)/', include([
                url(r'^management/$', group_element_year.update.management,
                    name="group_element_year_management"),

                url(r'^comment/$', group_element_year.update.UpdateGroupElementYearView.as_view(),
                    name="group_element_year_management_comment")
            ]))
        ])),

        url(r'^admission_conditions/$',
            education_group.education_group_year_admission_condition_edit,
            name='education_group_year_admission_condition_edit'),
        url(r'^admission_conditions/add_line$',
            education_group.education_group_year_admission_condition_add_line,
            name='education_group_year_admission_condition_add_line'),

        url(r'^admission_conditions/modify_text$',
            education_group.education_group_year_admission_condition_modify_text,
            name='education_group_year_admission_condition_modify_text'),

        url(r'^admission_conditions/get_text$',
            education_group.education_group_year_admission_condition_get_text,
            name='education_group_year_admission_condition_get_text'),

        url(r'^admission_conditions/remove_line$',
            education_group.education_group_year_admission_condition_remove_line,
            name='education_group_year_admission_condition_remove_line'),

        url(r'^admission_conditions/update_line$',
            education_group.education_group_year_admission_condition_update_line,
            name='education_group_year_admission_condition_update_line'),

        url(r'^admission_conditions/get_line$',
            education_group.education_group_year_admission_condition_get_line,
            name='education_group_year_admission_condition_get_line'),

        url(r'^delete/$', delete.DeleteGroupEducationView.as_view(), name="delete_education_group"),
        url(r'^group_content/', group_element_year.read.ReadEducationGroupTypeView.as_view(), name="group_content"),
        url(r'^pdf_content/(?P<language>[a-z\-]+)', pdf_content, name="pdf_content"),
    ])),
]
