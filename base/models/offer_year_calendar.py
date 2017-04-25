##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.contrib import admin
from base.models import offer_year
import datetime
from django.utils.translation import ugettext as _


class OfferYearCalendarAdmin(admin.ModelAdmin):
    list_display = ('academic_calendar', 'offer_year', 'start_date', 'end_date', 'changed')
    fieldsets = ((None, {'fields': ('offer_year', 'academic_calendar', 'start_date', 'end_date', 'customized')}),)
    raw_id_fields = ('offer_year',)
    search_fields = ['offer_year__acronym']
    list_filter = ('academic_calendar__academic_year', 'academic_calendar__title')


class OfferYearCalendar(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    academic_calendar = models.ForeignKey('AcademicCalendar')
    offer_year = models.ForeignKey('OfferYear')
    start_date = models.DateField(blank=True, null=True, db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    customized = models.BooleanField(default=False)

    def update_dates(self, start_date, end_date):
        if self.customized:  # case offerYearCalendar is already customized
            # We update the new start date
            # WARNING : this is TEMPORARY ; a solution for the sync from EPC to OSIS
            #           because the start_date for scores_encodings doesn't exist in EPC
            self.start_date = start_date
        else:
            self.start_date = start_date
            self.end_date = end_date
        self.save()

    def save(self, *args, **kwargs):
        academic_start_date = self.get_start_date()
        academic_end_date = self.get_end_date()
        if self.start_dates_set(academic_start_date) and self.start_date < academic_start_date:
            raise AttributeError(_('academic_start_date_error'))
        if self.end_dates_set(academic_end_date) and self.end_date > academic_end_date:
            raise AttributeError(_('academic_end_date_error'))
        if self.start_end_dates_set() and self.end_date < self.start_date:
            raise AttributeError(_('end_start_date_error'))
        super(OfferYearCalendar, self).save(*args, **kwargs)

    def start_end_dates_set(self):
        return self.start_date and self.end_date

    def end_dates_set(self, academic_end_date):
        return academic_end_date and self.end_date

    def start_dates_set(self, academic_start_date):
        return academic_start_date and self.start_date

    def get_end_date(self):
        if self.academic_calendar.end_date:
            return self.academic_calendar.end_date
        else:
            if self.offer_year.academic_year.end_date:
                return self.offer_year.academic_year.end_date
        return None

    def get_start_date(self):
        if self.academic_calendar.start_date:
            return self.academic_calendar.start_date
        else:
            if self.offer_year.academic_year.start_date:
                return self.offer_year.academic_year.start_date
        return None

    def __str__(self):
        return u"%s - %s" % (self.academic_calendar, self.offer_year)


def save_from_academic_calendar(academic_calendar):
    _raise_if_parameter_not_conform(academic_calendar)
    offer_year_calendars = find_by_academic_calendar(academic_calendar)
    if offer_year_calendars:
        for offer_year_calendar in offer_year_calendars:
            offer_year_calendar.update_dates(academic_calendar.start_date, academic_calendar.end_date)
    else:
        _create_from_academic_calendar(academic_calendar)


def _raise_if_parameter_not_conform(academic_calendar):
    if not academic_calendar:
        raise AttributeError('The parameter "academic_calendar" must be set (not none)')
    elif not academic_calendar.id:
        raise ValueError('Please make the academic calendar passed by parameter persitent (save it) '
                         'before calling this function')


def _create_from_academic_calendar(academic_calendar):
    academic_yr = academic_calendar.academic_year
    offer_years = offer_year.find_by_academic_year(academic_yr)
    for offer_yr in offer_years:
        offer_yr_calendar = OfferYearCalendar(academic_calendar=academic_calendar,
                                              offer_year=offer_yr,
                                              start_date=academic_calendar.start_date,
                                              end_date=academic_calendar.end_date)
        offer_yr_calendar.save()


def find_by_current_session_exam():
    return OfferYearCalendar.objects.filter(start_date__lte=timezone.now())\
        .filter(end_date__gte=timezone.now()).first()


def find_by_academic_calendar(academic_cal):
    return OfferYearCalendar.objects.filter(academic_calendar=academic_cal.id)


def find_offer_year_events(offer_yr):
    return OfferYearCalendar.objects.filter(offer_year=offer_yr,
                                            start_date__isnull=False,
                                            end_date__isnull=False).order_by('start_date',
                                                                             'academic_calendar__title')


def find_offer_year_calendars_by_academic_year(academic_yr):
    return OfferYearCalendar.objects.filter(academic_calendar__academic_year=academic_yr) \
        .order_by('academic_calendar', 'offer_year__acronym')


def find_by_id(offer_year_calendar_id):
    return OfferYearCalendar.objects.get(pk=offer_year_calendar_id)


def find_by_offer_year(offer_yr, academic_calendar_type=None):
    queryset = OfferYearCalendar.objects.filter(offer_year=offer_yr)
    if academic_calendar_type:
        queryset = queryset.filter(academic_calendar__reference=academic_calendar_type)
    return queryset


def find_latest_end_date_by_academic_calendar(academic_calendar_id):
    try:
        return OfferYearCalendar.objects.filter(academic_calendar_id=academic_calendar_id) \
            .filter(customized=True) \
            .filter(end_date__isnull=False) \
            .latest('end_date')
    except ObjectDoesNotExist:
        return None
