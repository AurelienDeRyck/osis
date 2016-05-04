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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from base.models import attribution, offer_year_calendar
from django.utils import timezone
from django.db.models import Count


SESSION_STATUS = (
    ('IDLE', _('idle')),
    ('OPEN', _('open')),
    ('CLOSED', _('closed')))


class SessionExamAdmin(admin.ModelAdmin):
    list_display = ('learning_unit_year', 'offer_year_calendar', 'number_session', 'status', 'changed')
    list_filter = ('status', 'number_session')
    raw_id_fields = ('learning_unit_year','offer_year_calendar')
    fieldsets = ((None, {'fields': ('learning_unit_year','number_session','status','offer_year_calendar')}),)
    search_fields = ['learning_unit_year__acronym']


class SessionExam(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    number_session = models.IntegerField()
    status = models.CharField(max_length=10,choices=SESSION_STATUS)
    learning_unit_year = models.ForeignKey('LearningUnitYear')
    offer_year_calendar = models.ForeignKey('OfferYearCalendar')
    progress = None

    def __str__(self):
        return u"%s - %d" % (self.learning_unit_year, self.number_session)


def current_session_exam():
    offer_calendar = offer_year_calendar.offer_year_calendar_by_current_session_exam()
    session_exam = SessionExam.objects.filter(offer_year_calendar=offer_calendar).first()
    return session_exam


def find_session_by_id(session_exam_id):
    return SessionExam.objects.get(pk=session_exam_id)


def find_session_exam_number():
    """
    :return: The current sessionExam number (based on the datetime.now() in offerYearCalendar).
    """
    sess_exam_number = SessionExam.objects.filter(offer_year_calendar__start_date__lte=timezone.now())\
                                          .filter(offer_year_calendar__end_date__gte=timezone.now())\
                                          .distinct('number_session')\
                                          .values('number_session')
    sess_exam_number = list(sess_exam_number) # Force evaluation of the queryset
    if len(sess_exam_number) > 1 :
        raise Exception("There are multiple exam sessions opened at this time now !")
    return sess_exam_number[0].get('number_session')

# def find_sessions_by_tutor(tutor, academic_year, learning_unit_id):
#     if learning_unit_id:
#         learning_units = attribution.Attribution.objects.filter(tutor=tutor).values('learning_unit')
#         return SessionExam.objects \
#             .filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit__in=learning_units) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#     else:
#         learning_units = attribution.Attribution.objects.filter(tutor=tutor).values('learning_unit')
#         return SessionExam.objects \
#             .filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit__in=learning_units) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())

#
# def find_sessions_by_offer(offer_year, academic_year, learning_unit_id):
#     if learning_unit_id:
#         return SessionExam.objects \
#             .filter(offer_year_calendar__offer_year__academic_year=academic_year) \
#             .filter(offer_year_calendar__offer_year=offer_year)\
#             .filter(learning_unit_year__learning_unit=learning_unit_id)\
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#     else:
#         return SessionExam.objects \
#             .filter(offer_year_calendar__offer_year__academic_year=academic_year) \
#             .filter(offer_year_calendar__offer_year=offer_year) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())


# def find_current_sessions_by_tutor(tutor, academic_year, learning_unit):
#     if learning_unit:
#
#         return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit=learning_unit) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#     else:
#         learning_units = attribution.Attribution.objects.filter(tutor=tutor).values('learning_unit')
#         return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit__in=learning_units) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())


# def find_sessions_by_offer_tutor(offer_year, academic_year, a_tutor):
#     if offer_year and a_tutor is None:
#         return SessionExam.objects \
#             .filter(offer_year_calendar__offer_year__academic_year=academic_year) \
#             .filter(offer_year_calendar__offer_year=offer_year)\
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#
#     if a_tutor and offer_year is None:
#         learning_units = attribution.Attribution.objects.filter(tutor=a_tutor).values('learning_unit')
#         return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit__in=learning_units) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#
#     if a_tutor and offer_year:
#         learning_units = attribution.Attribution.objects.filter(tutor=a_tutor).values('learning_unit')
#         return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit__in=learning_units) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now()) \
#             .filter(offer_year_calendar__offer_year=offer_year)


# def find_current_sessions_by_tutor_offer(tutor, academic_year,  learning_unit ,offer_year):
#      if learning_unit:
#
#         return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#             .filter(learning_unit_year__learning_unit=learning_unit) \
#             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#             .filter(offer_year_calendar__end_date__gte=timezone.now())
#      else:
#         if tutor and not offer_year:
#             learning_units = attribution.Attribution.objects.filter(tutor=tutor).values('learning_unit')
#             return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#                 .filter(learning_unit_year__learning_unit__in=learning_units) \
#                 .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#                 .filter(offer_year_calendar__end_date__gte=timezone.now())
#         else:
#             if offer_year and not tutor:
#
#                 return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#                     .filter(offer_year_calendar__offer_year=offer_year) \
#                     .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#                     .filter(offer_year_calendar__end_date__gte=timezone.now())
#             else:
#                 if offer_year and tutor:
#                     learning_units = attribution.Attribution.objects.filter(tutor=tutor).values('learning_unit')
#                     return SessionExam.objects.filter(learning_unit_year__academic_year=academic_year) \
#                             .filter(offer_year_calendar__offer_year=offer_year) \
#                             .filter(learning_unit_year__learning_unit__in=learning_units) \
#                             .filter(offer_year_calendar__start_date__lte=timezone.now()) \
#                             .filter(offer_year_calendar__end_date__gte=timezone.now())


def find_by_offer_years(offer_years):
    """
    :param offer_years: List of offer year from which to find the session_exams.
    :return: All session_exams, having minimum 1 exam_enrollment, for all offer years and for learning units passed in
             parameter.
    """
    queryset = SessionExam.objects

    queryset = queryset.annotate(number_of_exam_enrollments=Count('examenrollment')) \
                    .filter(number_of_exam_enrollments__gt=0) \
                    .filter(offer_year_calendar__offer_year__in=offer_years) \
                    .filter(offer_year_calendar__start_date__lte=timezone.now()) \
                    .filter(offer_year_calendar__end_date__gte=timezone.now())
    return queryset
