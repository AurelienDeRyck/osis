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
import datetime
from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from base.models import session_exam_calendar
from base.models.enums import number_session, academic_calendar_type


class SessionExamCalendarTest(TestCase):
    def setUp(self):
        tmp_academic_year = AcademicYearFactory()
        self.academic_calendar_1 = AcademicCalendarFactory.build(title="Submission of score encoding - 1",
                                                               start_date=datetime.date(2016, 10, 15),
                                                               end_date=datetime.date(2017, 1, 1),
                                                               academic_year=tmp_academic_year,
                                                               reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_2 = AcademicCalendarFactory.build(title="Submission of score encoding - 2",
                                                               start_date=datetime.date(2017, 3, 15),
                                                               end_date=datetime.date(2017, 6, 28),
                                                               academic_year=tmp_academic_year,
                                                               reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_3 = AcademicCalendarFactory.build(title="Submission of score encoding - 3",
                                                               start_date=datetime.date(2017, 10, 15),
                                                               end_date=datetime.date(2017, 12, 28),
                                                               academic_year=tmp_academic_year,
                                                               reference=academic_calendar_type.SCORES_EXAM_SUBMISSION)
        self.academic_calendar_1.save(functions=[])
        self.academic_calendar_2.save(functions=[])
        self.academic_calendar_3.save(functions=[])

    def test_number_exam_session_out_of_range(self):
        session_exam_calendar = SessionExamCalendarFactory.build(academic_calendar=self.academic_calendar_1,
                                                                 number_session=5)
        with self.assertRaises(ValidationError):
            session_exam_calendar.full_clean()

    def test_valid_number_exam_session(self):
        session_exam_calendar = SessionExamCalendarFactory.build(academic_calendar=self.academic_calendar_1,
                                                                 number_session=number_session.ONE)
        session_exam_calendar.full_clean()
        session_exam_calendar.save()

    def test_duplicate_exam_session(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1, number_session=number_session.ONE)
        with self.assertRaises(IntegrityError):
            SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1, number_session=number_session.ONE)

    def test_current_session_exam(self):
        session = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                                           number_session=number_session.ONE)

        self.assertEqual(session,session_exam_calendar.current_session_exam(date=datetime.date(2016,11,9)))

    def test_current_session_exam_none(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.ONE)

        self.assertIsNone(session_exam_calendar.current_session_exam(date=datetime.date(2017, 1, 5)))

    def test_find_session_exam_number(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.TWO)

        self.assertEqual(number_session.TWO,
                         session_exam_calendar.find_session_exam_number(date=datetime.date(2016, 11, 9)))

    def test_find_session_exam_number_none(self):
        SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.TWO)

        self.assertIsNone(session_exam_calendar.find_session_exam_number(date=datetime.date(2017, 1, 5)))


    def test_get_latest_session_exam(self):
        first = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_1,
                                   number_session=number_session.ONE)
        second = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_2,
                                   number_session=number_session.TWO)
        thrid = SessionExamCalendarFactory(academic_calendar=self.academic_calendar_3,
                                   number_session=number_session.THREE)

        self.assertIsNone(session_exam_calendar.get_latest_session_exam(date=datetime.date(2016, 11, 15)))
        self.assertEqual(first, session_exam_calendar.get_latest_session_exam(date=datetime.date(2017, 2, 10)))
        self.assertEqual(second, session_exam_calendar.get_latest_session_exam(date=datetime.date(2017, 8, 15)))
        self.assertEqual(thrid, session_exam_calendar.get_latest_session_exam(date=datetime.date(2018, 2, 2)))