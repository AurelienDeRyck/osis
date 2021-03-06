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

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _

from attribution.business import attribution_charge_new
from base import models as mdl
from base.business.learning_unit import get_cms_label_data, \
    get_same_container_year_components, find_language_in_settings, \
    CMS_LABEL_SPECIFICATIONS, get_achievements_group_by_language
from base.business.learning_units import perms as business_perms
from base.business.learning_units.comparison import get_keys, compare_learning_unit_years, \
    compare_learning_container_years, get_components_changes
from base.business.learning_units.perms import can_update_learning_achievement
from base.forms.learning_class import LearningClassEditForm
from base.forms.learning_unit_component import LearningUnitComponentEditForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models import education_group_year
from base.models.person import Person
from base.views.learning_units.common import get_learning_unit_identification_context, \
    get_common_context_learning_unit_year, get_text_label_translated
from cms.models import text_label
from . import layout
from base.business.learning_unit import get_learning_unit_comparison_context

ORGANIZATION_KEYS = ['REQUIREMENT_ENTITY', 'ADDITIONAL_REQUIREMENT_ENTITY_1', 'ADDITIONAL_REQUIREMENT_ENTITY_2',
                     'campus', 'organization']


@login_required
def learning_unit_identification(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_learning_unit_identification_context(learning_unit_year_id, person)

    learning_unit_year = context['learning_unit_year']

    if learning_unit_year.is_external():
        template = "learning_unit/external/read.html"
        permission = 'base.can_access_externallearningunityear'
    else:
        template = "learning_unit/identification.html"
        permission = 'base.can_access_learningunit'

    if not person.user.has_perm(permission):
        raise PermissionDenied
    return layout.render(request, template, context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id, get_object_or_404(Person, user=request.user))
    learn_unit_year = context["learning_unit_year"]
    group_elements_years = mdl.group_element_year.search(child_leaf=learn_unit_year) \
        .select_related("parent", "child_leaf").order_by('parent__partial_acronym')
    education_groups_years = [group_element_year.parent for group_element_year in group_elements_years]
    formations_by_educ_group_year = mdl.group_element_year.find_learning_unit_formations(education_groups_years,
                                                                                         parents_as_instances=True)
    context['formations_by_educ_group_year'] = formations_by_educ_group_year
    context['group_elements_years'] = group_elements_years

    context['root_formations'] = education_group_year.find_with_enrollments_count(learn_unit_year)

    return layout.render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']
    context['warnings'] = learning_unit_year.warnings
    data_components = get_same_container_year_components(context['learning_unit_year'], True)
    context['components'] = data_components.get('components')
    context['REQUIREMENT_ENTITY'] = data_components.get('REQUIREMENT_ENTITY')
    context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_1')
    context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_2')
    context['tab_active'] = 'components'
    context['can_manage_volume'] = business_perms.is_eligible_for_modification(context["learning_unit_year"], person)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_attributions(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    context['attribution_charge_news'] = \
        attribution_charge_new.find_attribution_charge_new_by_learning_unit_year(
            learning_unit_year=learning_unit_year_id)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']

    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_SPECIFICATIONS, user_language)

    fr_language = find_language_in_settings(settings.LANGUAGE_CODE_FR)
    en_language = find_language_in_settings(settings.LANGUAGE_CODE_EN)

    context.update({
        'form_french': LearningUnitSpecificationsForm(learning_unit_year, fr_language),
        'form_english': LearningUnitSpecificationsForm(learning_unit_year, en_language)
    })

    context.update(get_achievements_group_by_language(learning_unit_year))
    context.update({'LANGUAGE_CODE_FR': settings.LANGUAGE_CODE_FR, 'LANGUAGE_CODE_EN': settings.LANGUAGE_CODE_EN})
    context['can_update_learning_achievement'] = can_update_learning_achievement(learning_unit_year, person)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/specifications.html", context)


@login_required
@permission_required('base.can_edit_learningunit_specification', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_specifications_edit(request, learning_unit_year_id):
    if request.method == 'POST':
        form = LearningUnitSpecificationsEditForm(request.POST)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_specifications",
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    label_name = request.GET.get('label')
    text_lb = text_label.get_by_name(label_name)
    language = request.GET.get('language')
    form = LearningUnitSpecificationsEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form

    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = get_text_label_translated(text_lb, user_language)
    context['language_translated'] = find_language_in_settings(language)
    return layout.render(request, "learning_unit/specifications_edit.html", context)


@login_required
@permission_required('base.change_learningcomponentyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_component_edit(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    learning_component_id = request.GET.get('learning_component_year_id')
    context['learning_component_year'] = mdl.learning_component_year.find_by_id(learning_component_id)

    if request.method == 'POST':
        form = LearningUnitComponentEditForm(request.POST,
                                             learning_unit_year=context['learning_unit_year'],
                                             instance=context['learning_component_year'])
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse(learning_unit_components,
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    form = LearningUnitComponentEditForm(learning_unit_year=context['learning_unit_year'],
                                         instance=context['learning_component_year'])
    form.load_initial()  # Load data from database
    context['form'] = form
    return layout.render(request, "learning_unit/component_edit.html", context)


@login_required
@permission_required('base.change_learningclassyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_class_year_edit(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    context.update(
        {'learning_class_year': mdl.learning_class_year.find_by_id(request.GET.get('learning_class_year_id')),
         'learning_component_year':
             mdl.learning_component_year.find_by_id(request.GET.get('learning_component_year_id'))})

    if request.method == 'POST':
        form = LearningClassEditForm(
            request.POST,
            instance=context['learning_class_year'],
            learning_unit_year=context['learning_unit_year'],
            learning_component_year=context['learning_component_year']
        )
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_components",
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    form = LearningClassEditForm(
        instance=context['learning_class_year'],
        learning_unit_year=context['learning_unit_year'],
        learning_component_year=context['learning_component_year']
    )
    form.load_initial()  # Load data from database
    context['form'] = form
    return layout.render(request, "learning_unit/class_edit.html", context)


def learning_unit_comparison(request, learning_unit_year_id):
    learning_unit_yr = get_object_or_404(mdl.learning_unit_year.LearningUnitYear.objects.all()
                                         .select_related('learning_unit', 'learning_container_year'),
                                         pk=learning_unit_year_id)
    context = get_learning_unit_comparison_context(learning_unit_yr)

    previous_academic_yr = mdl.academic_year.find_academic_year_by_year(learning_unit_yr.academic_year.year - 1)
    previous_lu = _get_learning_unit_year(previous_academic_yr, learning_unit_yr)
    previous_values = compare_learning_unit_years(learning_unit_yr, previous_lu)
    previous_lcy_values = compare_learning_container_years(learning_unit_yr.learning_container_year,
                                                           previous_lu.learning_container_year)

    next_academic_yr = mdl.academic_year.find_academic_year_by_year(learning_unit_yr.academic_year.year + 1)
    next_lu = _get_learning_unit_year(next_academic_yr, learning_unit_yr)
    next_values = compare_learning_unit_years(learning_unit_yr, next_lu)
    next_lcy_values = compare_learning_container_years(learning_unit_yr.learning_container_year,
                                                       next_lu.learning_container_year)
    previous_context = get_learning_unit_comparison_context(previous_lu)
    next_context = get_learning_unit_comparison_context(next_lu)

    context.update(
        {'previous_values': previous_values,
         'previous_academic_yr': previous_academic_yr,
         'next_academic_yr': next_academic_yr,
         'next_values': next_values,
         'fields': get_keys(list(previous_values.keys()), list(next_values.keys())),
         'entity_changes': _get_changed_organization(context,
                                                     previous_context,
                                                     next_context),
         'fields_lcy': get_keys(list(previous_lcy_values.keys()), list(next_lcy_values.keys())),
         'previous_lcy_values': previous_lcy_values,
         'next_lcy_values': next_lcy_values,
         'components_comparison': get_components_changes(previous_context['components'],
                                                         context['components'],
                                                         next_context['components'])
         })
    return layout.render(request, "learning_unit/comparison.html", context)


def _get_learning_unit_year(academic_yr, learning_unit_yr):
    learning_unit_years = mdl.learning_unit_year.search(learning_unit=learning_unit_yr.learning_unit,
                                                        academic_year_id=academic_yr.id)
    if learning_unit_years.exists():
        return learning_unit_years.first()
    return None


def _get_changed_organization(context, context_prev, context_next):
    data = {}
    for key_value in ORGANIZATION_KEYS:
        if _has_changed(context, context_next, context_prev, key_value):
            translated_key = _('learning_location') if key_value == "campus" else _(key_value.lower())
            data.update({translated_key: {'prev': context_prev.get(key_value),
                                          'current': context.get(key_value),
                                          'next': context_next.get(key_value)}
                         })

    return collections.OrderedDict(sorted(data.items()))


def _has_changed(data_reference, data_1, data_2, key):
    return data_reference.get(key) != data_1.get(key) or data_reference.get(key) != data_2.get(key)
