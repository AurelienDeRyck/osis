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
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from django.utils.translation import ugettext_lazy as _

from base import models as mdl

PAGE_SIZE = A4
MARGIN_SIZE = 15 * mm
COLS_WIDTH = [25*mm,50*mm,50*mm,25*mm,25*mm]
STUDENTS_PER_PAGE = 24




def add_header_footer(canvas, doc):
    """
    Add the page number
    """
    styles = getSampleStyleSheet()
    # Save the state of our canvas so we can draw on it
    canvas.saveState()

    # Header
    header_building(canvas, doc, styles)

    # Footer
    footer_building(canvas, doc, styles)

    # Release the canvas
    canvas.restoreState()


def print_notes(academic_year, list_exam_enrollment):
    """
    Create a multi-page document
    :param academic_year: An object AcademicYear
    :param list_exam_enrollment: List of examEnrollments to print on the PDF.
    """
    filename = "%s.pdf" % _('scores_sheet')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=PAGE_SIZE,
                            rightMargin=MARGIN_SIZE,
                            leftMargin=MARGIN_SIZE,
                            topMargin=85,
                            bottomMargin=18)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    content = []

    list_notes_building(academic_year, list_exam_enrollment, styles, content)

    doc.build(content, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def header_building(canvas, doc, styles):
    a = Image(settings.LOGO_INSTITUTION_URL, width=15*mm, height=20*mm)

    p = Paragraph('''
                    <para align=center>
                        <font size=16>%s</font>
                    </para>''' % (_('scores_transcript')), styles["BodyText"])

    data_header = [[a, '%s' % _('ucl_denom_location'), p], ]

    t_header = Table(data_header, [30*mm, 100*mm, 50*mm])

    t_header.setStyle(TableStyle([]))

    w, h = t_header.wrap(doc.width, doc.topMargin)
    t_header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)


def footer_building(canvas, doc, styles):
    pageinfo = _('scores_sheet')
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)


def _write_table_of_students(content, data):
    t = Table(data, COLS_WIDTH, repeatRows=1)
    t.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey)]))
    content.append(t)


def _write_legend(content, offer_year_calendar, learning_unit_year):
    end_date = ""
    if offer_year_calendar.end_date:
        end_date = offer_year_calendar.end_date.strftime('%d/%m/%Y')
    end_page_infos_building(content, end_date)
    legend_building(learning_unit_year, content)


def _build_key(rec_exam_enrollment):
    offer_year_id = rec_exam_enrollment.session_exam.offer_year_calendar.offer_year.id
    learning_unit_year_id = rec_exam_enrollment.session_exam.learning_unit_year.id
    return "%s %s" % (str(offer_year_id), str(learning_unit_year_id))


def list_notes_building(academic_year, list_exam_enrollment, styles, content):
    # Will contain lists of examEnrollments splitted by learningUnitYear and by Offeryear
    enrollments_by_learn_unit_and_offer = {} # {<learning_unit_year_id, offer_year_id> : <ExamEnrollment>}
    for exam_enroll in list_exam_enrollment:
        key = _build_key(exam_enroll)
        if key not in enrollments_by_learn_unit_and_offer.keys():
            enrollments_by_learn_unit_and_offer[key] = [exam_enroll]
        else:
            enrollments_by_learn_unit_and_offer[key].append(exam_enroll)

    # Sort by learningUnitYear.acronym then by Offeryear.acronym
    list_exam_enrollments = sorted(enrollments_by_learn_unit_and_offer.values(),
                                  key=lambda k: "%s %s" % (k[0].session_exam.learning_unit_year.acronym,
                                                           k[0].session_exam.offer_year_calendar.offer_year.acronym))

    for exam_enrollments in list_exam_enrollments:
        data = headers_table()
        students_printed = 0
        enrollments_to_print = len(exam_enrollments)
        for exam_enroll in exam_enrollments:
            # 1. Getting informations from the student (noma, firstname, etc...)
            student = exam_enroll.learning_unit_enrollment.student
            person = mdl.person.find_by_id(student.person.id)
            score = None
            if not (exam_enroll.score_final is None):
                if exam_enroll.session_exam.learning_unit_year.decimal_scores:
                    score = "{0:.2f}".format(exam_enroll.score_final)
                else:
                    score = "{0:.0f}".format(exam_enroll.score_final)
            justification = ""
            if exam_enroll.justification_final:
                justification = mdl.exam_enrollment.get_letter_justication_type(exam_enroll.justification_final)
            sc = ""
            if score:
                sc = "%s" % score

            # 2. Append the examEnrollment to the table 'data'
            data.append([student.registration_id,
                         Paragraph(person.last_name, styles['Normal']),
                         Paragraph(person.first_name, styles['Normal']),
                         sc,
                         Paragraph(justification, styles['Normal'])])

            students_printed += 1
            enrollments_to_print -= 1

            if students_printed == STUDENTS_PER_PAGE or enrollments_to_print == 0:
                students_printed = 0
                offer_year_calendar = exam_enroll.session_exam.offer_year_calendar
                # Print a complete PDF sheet
                # 3. Write header
                main_data(academic_year,
                          exam_enroll.session_exam,
                          styles,
                          offer_year_calendar.offer_year, content)
                # 4. Adding the complete table of examEnrollments to the PDF sheet
                _write_table_of_students(content, data)

                # 5. Write Legend
                _write_legend(content, offer_year_calendar, exam_enroll.session_exam.learning_unit_year)

                # 6. New Page
                content.append(PageBreak())

                # 7. New headers_table in variable 'data' with headers ('noma', 'firstname', 'lastname'...)
                #    in case there's one more page after this one
                data = headers_table()


def legend_building(learning_unit_year, content):
    p = ParagraphStyle('legend')
    p.textColor = 'grey'
    p.borderColor = 'grey'
    p.borderWidth = 1
    p.alignment = TA_CENTER
    p.fontSize = 8
    p.borderPadding = 5

    legend_text = _('justification_legend') % mdl.exam_enrollment.justification_label_authorized()
    legend_text += "<br/>%s" % (str(_('score_legend') % "0 - 20"))
    if not learning_unit_year.decimal_scores:
        legend_text += "<br/><font color=red>%s</font>" % _('unauthorized_decimal_for_this_activity')

    legend_text += '''<br/> %s : <a href="%s"><font color=blue><u>%s</u></font></a>''' \
                   % (_("in_accordance_to_regulation"), _("link_to_RGEE"), _("link_to_RGEE"))
    content.append(Paragraph('''
                            <para>
                                %s
                            </para>
                            ''' % legend_text, p))


def headers_table():
    data = [['''%s''' % _('registration_number'),
             '''%s''' % _('lastname'),
             '''%s''' % _('firstname'),
             '''%s''' % _('numbered_score'),
             '''%s''' % _('justification')]]
    return data


def get_data_coordinator(learning_unit_year, styles):
    coordinator = mdl.tutor.find_responsible(learning_unit_year.learning_unit)
    p_coord_location = Paragraph('''''', styles["Normal"])
    p_coord_address = Paragraph('''''', styles["Normal"])
    p_responsible = Paragraph('<b>%s :</b>' % _('learning_unit_responsible'), styles["Normal"])
    if coordinator:
        p_coord_name = Paragraph(
            '%s %s' % (coordinator.person.last_name, coordinator.person.first_name),
            styles["Normal"])
        coordinator_address = mdl.person_address.find_by_person_label(coordinator.person, 'PROFESSIONAL')
        if coordinator_address:
            p_coord_location = Paragraph('''%s''' % coordinator_address.location, styles["Normal"])
            if coordinator_address.postal_code or coordinator_address.city:
                p_coord_address = Paragraph(
                    '''%s %s''' % (coordinator_address.postal_code, coordinator_address.city),
                    styles["Normal"])
    else:
        p_coord_name = Paragraph('%s' % _('none'), styles["Normal"])

    return [[p_responsible], [p_coord_name], [p_coord_location], [p_coord_address]]


def main_data(academic_year, session_exam, styles, offer, content):
    learning_unit_year = session_exam.learning_unit_year

    # We add first a blank line
    content.append(Paragraph('''
        <para spaceb=20>
            &nbsp;
        </para>
        ''', ParagraphStyle('normal')))

    text_left_style = ParagraphStyle('structure_header')
    text_left_style.alignment = TA_LEFT
    text_left_style.fontSize = 10
    p_struct_name = Paragraph('%s' % offer.recipient if offer.recipient else '',
                              styles["Normal"])

    p_struct_location = Paragraph('%s' % offer.location if offer.location else '',
                                  styles["Normal"])
    p_struct_address = Paragraph('%s %s' % (offer.postal_code if offer.postal_code else '',
                                            offer.city if offer.city else ''),
                                 styles["Normal"])
    phone_fax_data = ""
    if offer.phone:
        phone_fax_data += "%s : %s" % (_('phone'), offer.phone)
    if offer.fax:
        if offer.phone:
            phone_fax_data += " - "
        phone_fax_data += "%s : %s" % (_('fax'), offer.fax)
    p_phone_fax_data = Paragraph('%s' % phone_fax_data,
                                 styles["Normal"])

    data_structure = [[p_struct_name],
                      [p_struct_location],
                      [p_struct_address],
                      [p_phone_fax_data]]

    header_coordinator_structure = [[get_data_coordinator(learning_unit_year, styles), data_structure]]
    table_header = Table(header_coordinator_structure, colWidths='*')
    table_header.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    content.append(table_header)

    p = ParagraphStyle('right_page_header')
    p.alignment = TA_RIGHT
    p.fontSize = 10

    deliberation_date = mdl.offer_year_calendar.find_deliberation_date(offer, session_exam.number_session)
    if deliberation_date:
        deliberation_date = deliberation_date.strftime("%d/%m/%Y")
    else:
        deliberation_date = '-'
    content.append(Paragraph('%s : %s' % (_('deliberation_date'), deliberation_date), styles["Normal"]))
    content.append(Paragraph('%s : %s  - Session : %d' % (_('academic_year'), str(academic_year), session_exam.number_session), text_left_style))
    # content.append(Paragraph('Session : %d' % session_exam.number_session, text_left_style))
    content.append(Paragraph("<strong>%s : %s</strong>" % (learning_unit_year.acronym, learning_unit_year.title),
                             styles["Normal"]))
    content.append(Paragraph('''<b>%s : %s</b>''' % (_('program'), offer.acronym), styles["Normal"]))
    content.append(Paragraph('''
        <para spaceb=2>
            &nbsp;
        </para>
        ''', ParagraphStyle('normal')))


def end_page_infos_building(content, end_date):
    p = ParagraphStyle('info')
    p.fontSize = 10
    p.alignment = TA_LEFT
    content.append(Paragraph(_("return_doc_to_administrator") % end_date
                             , p))
    content.append(Paragraph('''
                            <para spaceb=5>
                                &nbsp;
                            </para>
                            ''', ParagraphStyle('normal')))
    p_signature = ParagraphStyle('info')
    p_signature.fontSize = 10
    paragraph_signature = Paragraph('''
                    <font size=10>%s ...................................... , </font>
                    <font size=10>%s ..../..../.......... &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font>
                    <font size=10>%s</font>
                   ''' % (_('done_at'), _('the'), _('signature')), p_signature)
    content.append(paragraph_signature)
    content.append(Paragraph('''
        <para spaceb=2>
            &nbsp;
        </para>
        ''', ParagraphStyle('normal')))
