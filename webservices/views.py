import collections

import bs4
from django.http import Http404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.offer_year_entity import OfferYearEntity
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel


LANGUAGES = {'fr': 'fr-be', 'en': 'en'}
ENTITY = 'offer_year'

Context = collections.namedtuple(
    'Context',
    ['year', 'language', 'acronym', 'title', 'academic_year', 'education_group_year']
)


class JSONNotFoundResponse(Response):
    def __init__(self):
        super().__init__({'detail': 'Not found.'},
                         content_type='application/json',
                         status=404)


def find_translated_labels_for_entity_and_language(entity, language):
    queryset = TranslatedTextLabel.objects.filter(
        text_label__entity=entity, language=language)

    return {item.text_label.label: item.label for item in queryset}


def get_common_education_group(academic_year, language, acronym):
    education_group_year = EducationGroupYear.objects.filter(
        academic_year=academic_year, acronym__iexact=acronym).first()

    values = {}
    if education_group_year:
        queryset = TranslatedText.objects.filter(
            entity='offer_year',
            reference=education_group_year.id,
            language=language)

        for translated_text in queryset.order_by('text_label__order'):
            label = translated_text.text_label.label

            values[label] = translated_text.text
    return values


def get_entity(education_group_year):
    from base.models.enums.offer_year_entity_type import ENTITY_ADMINISTRATION
    offer_year_entity = OfferYearEntity.objects.filter(education_group_year=education_group_year,
                                                       type=ENTITY_ADMINISTRATION)
    entity = offer_year_entity.first().entity

    from django.forms import model_to_dict

    result = model_to_dict(entity)
    result['acronym'] = entity.most_recent_acronym

    keeps = ('city', 'fax', 'location', 'phone', 'postal_code', 'website', 'acronym')
    return {
        k: v for k, v in result.items() if k in keeps
    }

def get_cleaned_parameters(type_acronym):
    def get_cleaned_parameters(function):
        def wrapper(request, year, language, acronym):
            year = to_int_or_404(year)

            if language not in LANGUAGES:
                raise Http404

            academic_year = get_object_or_404(AcademicYear, year=year)

            parameters = {
                'academic_year': academic_year,
                'partial_acronym__iexact' if type_acronym == 'partial' else 'acronym__iexact': acronym
            }

            education_group_year = get_object_or_404(EducationGroupYear, **parameters)
            iso_language = LANGUAGES[language]

            title = get_title_of_education_group_year(education_group_year, iso_language)

            context = Context(
                year=year,
                language=iso_language,
                acronym=acronym,
                title=title,
                academic_year=academic_year,
                education_group_year=education_group_year
            )

            return function(request, context)


        return wrapper
    return get_cleaned_parameters


def to_int_or_404(year):
    try:
        return int(year)
    except:
        raise Http404


@api_view(['GET'])
@renderer_classes((JSONRenderer, ))
@get_cleaned_parameters(type_acronym='acronym')
def ws_catalog_offer(request, context):
    translated_labels = find_translated_labels_for_entity_and_language(ENTITY, context.language)
    description = get_description(context.education_group_year, context.language, context.title, context.year)

    common_terms = get_common_education_group(context.academic_year, context.language, 'common')
    section_append = description['sections'].append

    has_section = collections.defaultdict(bool)

    queryset = find_translated_texts_by_entity_and_language(context.education_group_year,ENTITY, context.language)

    for translated_text in queryset:
        insert_section(common_terms, has_section, section_append, translated_labels, translated_text)

    insert_missing_sections(common_terms, context, has_section, section_append)

    return Response(description, content_type='application/json')


def insert_missing_sections(common_terms, context, has_section, section_append):
    sections = [
        ('programme', 'agregations', 'programme', 'Programme'),
        ('caap', 'caap', 'caap', 'Caap'),
        ('prerequis', 'prerequis', 'prerequis', 'Prerequis')
    ]
    for section, common_term, name, label in sections:
        if has_section[section]:
            continue

        term = common_terms.get(common_term)
        if term:
            section_append({
                'id': name,
                'label': label,
                'content': term,
            })
    if context.acronym.lower().endswith('2m'):
        section_append({
            'id': 'finalite-didactique-commun',
            'label': 'Finalite Didactique',
            'content': common_terms['finalites_didactiques']
        })


def insert_section(common_terms, has_section, section_append, translated_labels, translated_text):
    label = get_label(translated_labels, translated_text)
    name = translated_text.text_label.label
    content = translated_text.text
    if name in ('caap', 'prerequis'):
        content = normalize_caap_or_prerequis(common_terms, content, has_section, name)

    elif name == 'programme':
        content = normalize_program(common_terms, content, has_section, name)

    elif name == 'module_complementaire':
        content = normalize_module_complementaire(common_terms, content, has_section, name)
    section_append({
        'id': name,
        'label': label,
        'content': content,
    })


def find_translated_texts_by_entity_and_language(education_group_year, entity, iso_language):
    queryset = TranslatedText.objects.filter(
        entity=entity,
        reference=education_group_year.id,
        language=iso_language)

    return queryset.order_by('text_label__order')


def get_description(education_group_year, language, title, year):
    return {
        'language': language,
        'acronym': education_group_year.acronym,
        'title': title,
        'year': year,
        'sections': [],
    }


def normalize_module_complementaire(common_terms, content, has_section, name):
    has_section[name] = True
    term = common_terms.get('module_compl')
    if term:
        soup_term = bs4.BeautifulSoup(term, 'html.parser')
        new_tag = soup_term.new_tag('div', **{'class': 'info'})
        new_tag.append(soup_term)
        soup = bs4.BeautifulSoup(content, 'html.parser')
        soup.insert(0, new_tag)

        content = str(soup)
    return content


def normalize_program(common_terms, content, has_section, name):
    has_section[name] = True
    term = common_terms.get('agregations')
    if term:
        soup_term = bs4.BeautifulSoup(term, 'html.parser')
        soup = bs4.BeautifulSoup(content, 'html.parser')
        soup.insert(0, soup_term)

        content = str(soup)
    return content


def normalize_caap_or_prerequis(common_terms, content, has_section, name):
    has_section[name] = True
    term = common_terms.get(name)
    if term:
        soup_term = bs4.BeautifulSoup(term, 'html.parser')
        soup = bs4.BeautifulSoup(content, 'html.parser')
        nodes = soup.select('div.part2')
        if nodes:
            part = nodes[0]
            part.insert_before(soup_term)
        else:
            soup.append(soup_term)
        content = str(soup)
    return content


def get_label(translated_labels, translated_text):
    label = translated_labels.get(translated_text.text_label.label)
    if not label:
        label = translated_text.text_label.label
        if label.startswith('welcome_'):
            label = label.split('_')[-1]
        label = ' '.join(label.title().split('_'))
    return label


@api_view(['GET'])
@renderer_classes((JSONRenderer,))
@get_cleaned_parameters(type_acronym='partial')
def ws_catalog_group(request, context):
    translated_labels = find_translated_labels_for_entity_and_language(ENTITY, context.language)

    description = get_description(context.education_group_year,
                                  context.language,
                                  context.title,
                                  context.year)

    description['partial_acronym'] = context.education_group_year.partial_acronym

    section_append = description['sections'].append

    queryset = find_translated_texts_by_entity_and_language(context.education_group_year,
                                                            ENTITY,
                                                            context.language)

    for translated_text in queryset:
        insert_section_group(section_append, translated_labels, translated_text)

    return Response(description, content_type='application/json')


def insert_section_group(section_append, translated_labels, translated_text):
    label = translated_labels.get(translated_text.text_label.label)
    content = translated_text.text
    name = translated_text.text_label.label
    section_append({
        'id': name,
        'label': label,
        'content': content,
    })


def get_title_of_education_group_year(education_group_year, iso_language):
    if iso_language == 'fr-be':
        title = education_group_year.title
    else:
        title = education_group_year.title_english
    return title
