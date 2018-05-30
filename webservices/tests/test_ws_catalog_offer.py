import json

from django.test import TestCase
from prettyprinter import prettyprinter

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from webservices.tests.helper import Helper
from webservices.utils import convert_sections_list_of_dict_to_dict


class CatalogOfferWebServiceTestCase(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'

    def test_year_not_found(self):
        response = self._get_response(1990, 'fr', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_language_not_found(self):
        response = self._get_response(2017, 'ch', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_acronym_not_found(self):
        response = self._get_response(2017, 'fr', 'XYZ')
        self.assertEqual(response.status_code, 404)

    def _test_education_group_year_with_translation(self, language, iso_language):
        values = self._create_records_for_test_education_group_year(iso_language)

        academic_year, education_group_year, text_label, translated_text, translated_text_label = values

        response = self._get_response(academic_year.year, language, education_group_year.acronym)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        response_json = json.loads(response.content.decode('utf-8'))

        context = {
            'academic_year': academic_year,
            'education_group_year': education_group_year,
            'language': language,
            'text_label': text_label,
            'translated_text': translated_text,
            'translated_text_label': translated_text_label
        }

        fake_response = self._mock_response_dictionary(**context)

        self.assertDictEqual(response_json, fake_response)

    def _create_records_for_test_education_group_year(self, iso_language):
        academic_year = AcademicYearFactory()
        education_group_year = EducationGroupYearFactory(academic_year=academic_year)
        text_label = TextLabelFactory(entity=OFFER_YEAR)
        translated_text_label = TranslatedTextLabelFactory(language=iso_language,
                                                           text_label=text_label)
        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=education_group_year.id,
            language=iso_language,
        )
        return (academic_year, education_group_year,
                text_label, translated_text, translated_text_label)

    def _mock_response_dictionary(self, **kwargs):
        return {
            'acronym': kwargs['education_group_year'].acronym,
            'title': kwargs['education_group_year'].title_english,
            'year': kwargs['academic_year'].year,
            'language': kwargs['language'],
            'sections': [
                {
                    'content': kwargs['translated_text'].text,
                    'label': kwargs['translated_text_label'].label,
                    'id': kwargs['text_label'].label
                }
            ]
        }

    def test_education_group_year_with_translation_fr(self):
        self._test_education_group_year_with_translation('fr', 'fr-be')

    def test_education_group_year_with_translation_en(self):
        self._test_education_group_year_with_translation('en', 'en')


class WsCatalogOfferCommonTestCase(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'

    TERMS = [
        ('finalites_didactiques', 'Finalités Didactiques'),
        ('caap', 'Caap'),
        ('prerequis', 'Prérequis'),
        ('module_complementaire', 'Module Complémentaire'),
        ('agregations', 'Agregations')
    ]

    def setUp(self):
        super().setUp()

        self.iso_language, self.language = 'fr-be', 'fr'

        self.education_group_year = EducationGroupYearFactory()

        self.common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=self.education_group_year.academic_year
        )

        self.setup_common_terms()

    def setup_common_terms(self):
        for term, label in self.TERMS:
            text_label = TextLabelFactory(entity=OFFER_YEAR, label=term)
            TranslatedTextLabelFactory(
                text_label=text_label,
                language=self.iso_language,
                label=label
            )

            TranslatedTextRandomFactory(
                language=self.iso_language,
                text_label=text_label,
                entity=OFFER_YEAR,
                reference=self.common_education_group_year.id,
                text='<tag>{term}</tag>'.format(term=term)
            )

    def get_common_text_label(self, term):
        return TextLabel.objects.get(entity=OFFER_YEAR, label=term)

    def get_common_translated_text(self, term):
        return TranslatedText.objects.get(
            language=self.iso_language,
            text_label__label=term,
            entity=OFFER_YEAR,
            reference=self.common_education_group_year.id
        )

    def get_common_translated_text_label(self, term):
        return TranslatedTextLabel.objects.get(
            text_label__label=term,
            language=self.iso_language,
        )

    def get_section_for_common_term(self, term):
        key_id = term
        if term != 'agregations':
            key_id = self.get_common_text_label(term).label + '-commun'

        return {
            'label': self.get_common_translated_text_label(term).label,
            'content': self.get_common_translated_text(term).text,
            'id': key_id,
        }

    def create_text_label_and_translation(self, term, label):
        text_label = TextLabelFactory(entity=OFFER_YEAR, label=term)
        translated_text_label = TranslatedTextLabelFactory(
            text_label=text_label,
            language=self.iso_language,
            label=label
        )

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=self.education_group_year.id,
            language=self.iso_language
        )

        return translated_text_label, translated_text

    def get_section_for_term(self, translated_text_label, translated_text):
        return {
            'content': translated_text.text,
            'id': translated_text.text_label.label,
            'label': translated_text_label.label,
        }

    def test_header_of_message(self):
        response = self._get_response(self.education_group_year.academic_year.year,
                                      self.language,
                                      self.education_group_year.acronym)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        self.assertDictEqual(response_json, {
            'acronym': self.education_group_year.acronym,
            'language': self.language,
            'title': self.education_group_year.title,
            'year': self.education_group_year.academic_year.year,
            'sections': [],
        })

    def test_education_group_year_caap(self):
        text_label = self.get_common_text_label('caap')
        translated_text_label = self.get_common_translated_text_label('caap')

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=self.education_group_year.id,
            language=self.iso_language,
        )

        response = self._get_response(
            self.education_group_year.academic_year.year,
            self.language,
            self.education_group_year.acronym
        )

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_term(translated_text_label, translated_text),
            self.get_section_for_common_term('caap'),
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)

    def test_education_group_year_prerequis(self):
        text_label = self.get_common_text_label('prerequis')
        translated_text_label = self.get_common_translated_text_label('prerequis')

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=self.education_group_year.id,
            language=self.iso_language
        )

        response = self._get_response(
            self.education_group_year.academic_year.year,
            self.language,
            self.education_group_year.acronym
        )

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_term(translated_text_label, translated_text),
            self.get_section_for_common_term('prerequis'),
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)

    def test_education_group_year_module_complementaire(self):
        text_label = self.get_common_text_label('module_complementaire')
        translated_text_label = self.get_common_translated_text_label('module_complementaire')

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            language=self.iso_language,
            entity=OFFER_YEAR,
            reference=self.education_group_year.id,
        )

        response = self._get_response(
            self.education_group_year.academic_year.year,
            self.language,
            self.education_group_year.acronym,
        )

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_term(translated_text_label, translated_text),
            self.get_section_for_common_term('module_complementaire'),
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)


    def test_education_group_year_programme(self):
        translated_text_label, translated_text = self.create_text_label_and_translation('programme', 'Programme')

        response = self._get_response(
            self.education_group_year.academic_year.year,
            self.language,
            self.education_group_year.acronym
        )

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_term(translated_text_label, translated_text),
            self.get_section_for_common_term('agregations'),
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)


class WsCatalogOfferCommonTestCaseFor2M(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'

    TERMS = [
        ('finalites_didactiques', 'Finalités Didactiques'),
        ('caap', 'Caap'),
    ]

    def setUp(self):
        super().setUp()

        self.iso_language, self.language = 'fr-be', 'fr'

        self.education_group_year = EducationGroupYearFactory(acronym='ACTU2M')

        self.common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=self.education_group_year.academic_year
        )

        self.setup_common_terms()

    def setup_common_terms(self):
        for term, label in self.TERMS:
            text_label = TextLabelFactory(entity=OFFER_YEAR, label=term)
            TranslatedTextLabelFactory(
                text_label=text_label,
                language=self.iso_language,
                label=label
            )

            TranslatedTextRandomFactory(
                language=self.iso_language,
                text_label=text_label,
                entity=OFFER_YEAR,
                reference=self.common_education_group_year.id,
                text='<tag>{term}</tag>'.format(term=term)
            )

    def get_common_text_label(self, term):
        return TextLabel.objects.get(entity=OFFER_YEAR, label=term)

    def get_common_translated_text(self, term):
        return TranslatedText.objects.get(
            language=self.iso_language,
            text_label__label=term,
            entity=OFFER_YEAR,
            reference=self.common_education_group_year.id
        )

    def get_common_translated_text_label(self, term):
        return TranslatedTextLabel.objects.get(
            text_label__label=term,
            language=self.iso_language,
        )

    def get_section_for_common_term(self, term):
        key_id = term
        if term != 'agregations':
            key_id = self.get_common_text_label(term).label + '-commun'

        return {
            'label': self.get_common_translated_text_label(term).label,
            'content': self.get_common_translated_text(term).text,
            'id': key_id,
        }

    def create_text_label_and_translation(self, term, label):
        text_label = TextLabelFactory(entity=OFFER_YEAR, label=term)
        translated_text_label = TranslatedTextLabelFactory(
            text_label=text_label,
            language=self.iso_language,
            label=label
        )

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=self.education_group_year.id,
            language=self.iso_language
        )

        return translated_text_label, translated_text

    def get_section_for_term(self, translated_text_label, translated_text):
        return {
            'content': translated_text.text,
            'id': translated_text.text_label.label,
            'label': translated_text_label.label,
        }

    def test_header_of_message(self):
        response = self._get_response(self.education_group_year.academic_year.year,
                                      self.language,
                                      self.education_group_year.acronym)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        self.assertDictEqual(response_json, {
            'acronym': self.education_group_year.acronym,
            'language': self.language,
            'title': self.education_group_year.title,
            'year': self.education_group_year.academic_year.year,
            'sections': [
                self.get_section_for_common_term('finalites_didactiques')
            ],
        })

    def test_education_group_year_endswith_2m(self):
        response = self._get_response(self.education_group_year.academic_year.year,
                                      self.language,
                                      self.education_group_year.acronym)

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_common_term('finalites_didactiques')
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)

    def test_education_group_year_caap(self):
        text_label = self.get_common_text_label('caap')
        translated_text_label = self.get_common_translated_text_label('caap')

        translated_text = TranslatedTextRandomFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=self.education_group_year.id,
            language=self.iso_language,
        )

        response = self._get_response(
            self.education_group_year.academic_year.year,
            self.language,
            self.education_group_year.acronym
        )

        response_json = response.json()

        response_sections = convert_sections_list_of_dict_to_dict(
            response_json.pop('sections', [])
        )

        sections = [
            self.get_section_for_term(translated_text_label, translated_text),
            self.get_section_for_common_term('caap'),
            self.get_section_for_common_term('finalites_didactiques')
        ]

        sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertDictEqual(response_sections, sections)
