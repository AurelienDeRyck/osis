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
from django.contrib import admin
from internship.models import InternshipSpecialityGroup, InternshipSpecialityGroupMember
from .models import InternshipOffer, InternshipEnrollment, InternshipMaster, InternshipChoice, \
    Period, PeriodInternshipPlaces, InternshipSpeciality, Organization, \
    OrganizationAddress, InternshipStudentInformation, InternshipStudentAffectationStat, AffectationGenerationTime


class InternshipOfferAdmin(admin.ModelAdmin):
    list_display = ('organization','speciality', 'title', 'maximum_enrollments', 'master', 'selectable')
    fieldsets = ((None, {'fields': ('organization','speciality', 'title', 'maximum_enrollments', 'master', 'selectable')}),)
    raw_id_fields = ('organization','speciality')

admin.site.register(InternshipOffer, InternshipOfferAdmin)


class InternshipEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'internship_offer', 'place', 'period')
    fieldsets = ((None, {'fields': ('student', 'internship_offer', 'place', 'period')}),)
    raw_id_fields = ('student', 'internship_offer','place', 'period')

admin.site.register(InternshipEnrollment, InternshipEnrollmentAdmin)


class InternshipMasterAdmin(admin.ModelAdmin):
    list_display = ('reference', 'organization', 'first_name', 'last_name', 'civility', 'type_mastery', 'speciality')
    fieldsets = ((None, {'fields': ('reference', 'organization', 'first_name', 'last_name', 'civility', 'type_mastery', 'speciality')}),)
    raw_id_fields = ('organization',)

admin.site.register(InternshipMaster, InternshipMasterAdmin)


class InternshipChoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'organization', 'speciality', 'choice', 'internship_choice', 'priority')
    fieldsets = ((None, {'fields': ('student', 'organization', 'speciality', 'choice', 'internship_choice', 'priority')}),)
    raw_id_fields = ('student', 'organization', 'speciality')

admin.site.register(InternshipChoice, InternshipChoiceAdmin)


class PeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_start', 'date_end')
    fieldsets = ((None, {'fields': ('name', 'date_start', 'date_end')}),)

admin.site.register(Period, PeriodAdmin)


class PeriodInternshipPlacesAdmin(admin.ModelAdmin):
    list_display = ('period', 'internship', 'number_places')
    fieldsets = ((None, {'fields': ('period', 'internship', 'number_places')}),)
    raw_id_fields = ('period', 'internship')

admin.site.register(PeriodInternshipPlaces, PeriodInternshipPlacesAdmin)


class InternshipSpecialityAdmin(admin.ModelAdmin):
    list_display = ('learning_unit', 'name', 'acronym', 'mandatory', 'order_postion')
    fieldsets = ((None, {'fields': ('learning_unit', 'name', 'acronym', 'mandatory', 'order_postion')}),)
    raw_id_fields = ('learning_unit',)

admin.site.register(InternshipSpeciality, InternshipSpecialityAdmin)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'reference', 'type')
    fieldsets = ((None, {'fields': ('name', 'acronym', 'reference', 'website', 'type')}),)
    search_fields = ['acronym']

admin.site.register(Organization, OrganizationAdmin)


class OrganizationAddressAdmin(admin.ModelAdmin):
    list_display = ('organization', 'label', 'location', 'postal_code', 'city', 'country','latitude', 'longitude')
    fieldsets = ((None, {'fields': ('organization', 'label', 'location', 'postal_code', 'city', 'country', 'latitude', 'longitude')}),)
    raw_id_fields = ('organization',)

admin.site.register(OrganizationAddress, OrganizationAddressAdmin)


class InternshipStudentInformationAdmin(admin.ModelAdmin):
    list_display = ('person', 'location', 'postal_code', 'city', 'country', 'latitude', 'longitude', 'email', 'phone_mobile')
    fieldsets = ((None, {'fields': ('person', 'location', 'postal_code', 'city', 'latitude', 'longitude', 'country', 'email', 'phone_mobile')}),)
    raw_id_fields = ('person',)
    search_fields = ['person__user__username', 'person__last_name', 'person__first_name']

admin.site.register(InternshipStudentInformation, InternshipStudentInformationAdmin)


class InternshipStudentAffectationStatAdmin(admin.ModelAdmin):
    list_display = ('student', 'organization', 'speciality', 'period', 'choice', 'cost', 'consecutive_month', 'type_of_internship')
    fieldsets = ((None, {'fields': ('student', 'organization', 'speciality', 'period', 'choice', 'cost', 'consecutive_month', 'type_of_internship')}),)
    raw_id_fields = ('student', 'organization', 'speciality', 'period')

admin.site.register(InternshipStudentAffectationStat, InternshipStudentAffectationStatAdmin)


class AffectationGenerationTimeAdmin(admin.ModelAdmin):
    list_display = ('start_date_time', 'end_date_time', 'generated_by')
    fieldsets = ((None, {'fields': ('start_date_time', 'end_date_time', 'generated_by')}),)

admin.site.register(AffectationGenerationTime, AffectationGenerationTimeAdmin)


class InternshipSpecialityGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
    fieldsets = ((None, {'fields': ('name',)}),)

admin.site.register(InternshipSpecialityGroup, InternshipSpecialityGroupAdmin)


class InternshipSpecialityGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'speciality')
    fieldsets = ((None, {'fields' : ('group', 'speciality')}),)
    raw_id_fields = ('group', 'speciality')

admin.site.register(InternshipSpecialityGroupMember, InternshipSpecialityGroupMemberAdmin)