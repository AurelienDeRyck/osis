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
import collections
import re

from django.core.exceptions import SuspiciousOperation
from django.http import Http404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from base.models.education_group_year import EducationGroupYear
from cms.enums.entity_name import OFFER_YEAR
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.utils import convert_sections_to_list_of_dict

LANGUAGES = {'fr': 'fr-be', 'en': 'en'}
INTRO_PATTERN = r'intro-(?P<acronym>\w+)'
COMMON_PATTERN = r'(?P<section_name>\w+)-commun'


Context = collections.namedtuple(
    'Context',
    ['year', 'language', 'acronym',
     'title', 'description',
     'academic_year', 'education_group_year']
)


def new_description(education_group_year, language, title):
    return {
        'language': language,
        'acronym': education_group_year.acronym,
        'title': title,
        'year': int(education_group_year.academic_year.year),
        'sections': [],
    }


def get_title_of_education_group_year(education_group_year, iso_language):
    if iso_language == 'fr-be':
        title = education_group_year.title
    else:
        title = education_group_year.title_english
    return title


def validate_json_request(request, year, acronym):
    if request.content_type != 'application/json':
        raise SuspiciousOperation('Invalid JSON')

    request_json = request.data
    if 'anac' not in request_json or 'code_offre' not in request_json or 'sections' not in request_json:
        raise SuspiciousOperation('Invalid JSON')

    if year != int(request_json['anac']):
        raise SuspiciousOperation('Invalid JSON')

    if acronym.lower() != request_json['code_offre'].lower():
        raise SuspiciousOperation('Invalid JSON')

    if not all(isinstance(item, str) for item in request_json['sections']):
        raise SuspiciousOperation('Invalid JSON')


@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def ws_catalog_offer(request, year, language, acronym):
    # Validation
    education_group_year, iso_language, year = parameters_validation(acronym, language, year)

    validate_json_request(request, year, acronym)

    # Processing
    context = new_context(acronym, education_group_year, iso_language, language)
    items = request.data['sections']

    # sections = collections.OrderedDict()
    sections = process_message(context, education_group_year, items)

    context.description['sections'] = convert_sections_to_list_of_dict(sections)
    return Response(context.description, content_type='application/json')


def process_message(context, education_group_year, items):
    sections = collections.OrderedDict()
    for item in items:
        section = process_section(context, education_group_year, item)
        if section is not None:
            sections[item] = section
    return sections


def process_section(context, education_group_year, item):
    m_intro = re.match(INTRO_PATTERN, item)
    m_common = re.match(COMMON_PATTERN, item)
    if m_intro:
        egy = EducationGroupYear.objects.filter(partial_acronym__iexact=m_intro.group('acronym'),
                                                academic_year__year=context.year).first()

        text_label = TextLabel.objects.filter(entity=OFFER_YEAR, label='intro').first()

        return insert_section_if_checked(context, egy, text_label)
    elif m_common:
        egy = EducationGroupYear.objects.filter(acronym__iexact='common',
                                                academic_year__year=context.year).first()
        text_label = TextLabel.objects.filter(entity=OFFER_YEAR, label=m_common.group('section_name')).first()
        return insert_section_if_checked(context, egy, text_label)
    else:
        text_label = TextLabel.objects.filter(entity=OFFER_YEAR, label=item).first()
        if text_label:
            return insert_section(context, education_group_year, text_label)
    return None


def new_context(acronym, education_group_year, iso_language, language):
    title = get_title_of_education_group_year(education_group_year, iso_language)
    description = new_description(education_group_year, language, title)
    context = Context(
        acronym=acronym.upper(),
        year=int(education_group_year.academic_year.year),
        title=title,
        description=description,
        education_group_year=education_group_year,
        academic_year=education_group_year.academic_year,
        language=iso_language,
    )
    return context


def parameters_validation(acronym, language, year):
    year = int(year)
    iso_language = LANGUAGES.get(language)
    if not iso_language:
        raise Http404
    education_group_year = get_object_or_404(EducationGroupYear,
                                             acronym__iexact=acronym,
                                             academic_year__year=year)
    return education_group_year, iso_language, year


def insert_section(context, education_group_year, text_label):
    translated_text_label = TranslatedTextLabel.objects.filter(text_label=text_label, language=context.language).first()
    translated_text = TranslatedText.objects.filter(text_label=text_label,
                                                    language=context.language,
                                                    entity=text_label.entity,
                                                    reference=education_group_year.id).first()
    if translated_text_label and translated_text:
        return {'label': translated_text_label.label, 'content': translated_text.text}
    elif translated_text_label:
        return {'label': translated_text_label.label, 'content': None}
    return {'label': None, 'content': None}


def insert_section_if_checked(context, education_group_year, text_label):
    if education_group_year and text_label:
        return insert_section(context, education_group_year, text_label)
    return {'label': None, 'content': None}
