from unittest.mock import patch
from base.forms.education_group.group import GroupModelForm, GroupForm
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories
from base.models.group_element_year import GroupElementYear
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.forms.education_group.test_common import EducationGroupYearMixin, _get_valid_post_data
from django.test import TestCase


class TestGroupModelForm(EducationGroupYearMixin):

    def setUp(self):
        self.education_group_type = EducationGroupTypeFactory(category=education_group_categories.GROUP)
        self.form_class = GroupModelForm
        super(TestGroupModelForm, self).setUp(education_group_type=self.education_group_type)

    def test_fields(self):
        fields = ("acronym", "partial_acronym", "education_group_type", "title", "title_english", "credits",
                  "main_teaching_campus", "academic_year", "remark", "remark_english", "min_credits", "max_credits",
                  "administration_entity")

        form = GroupModelForm(parent=None)
        self.assertCountEqual(tuple(form.fields.keys()), fields)

    def test_init_academic_year_field(self):
        self._test_init_academic_year_field(self.form_class)

    def test_init_education_group_type_field(self):
        self._test_init_education_group_type_field(self.form_class, education_group_categories.GROUP)

    def test_preselect_entity_version_from_entity_value(self):
        self._test_preselect_entity_version_from_entity_value(self.form_class)


class TestGroupForm(TestCase):
    def setUp(self):
        self.category = education_group_categories.GROUP
        self.expected_educ_group_year, self.post_data = _get_valid_post_data(self.category)

    def test_create(self):
        form = GroupForm(data=self.post_data, parent=None)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save()

        self.assertEqual(education_group_year.education_group.start_year,
                         self.expected_educ_group_year.academic_year.year)
        self.assertIsNone(education_group_year.education_group.end_year)

    @patch('base.models.education_group_type.find_authorized_types', return_value=EducationGroupType.objects.all())
    def test_create_with_parent(self, mock_find_authorized_types):
        parent = EducationGroupYearFactory()
        form = GroupForm(data=self.post_data, parent=parent)

        self.assertTrue(form.is_valid(), form.errors)

        education_group_year = form.save()

        self.assertTrue(GroupElementYear.objects.get(child_branch=education_group_year, parent=parent))