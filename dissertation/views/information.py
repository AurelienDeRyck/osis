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
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from dissertation.models.adviser import Adviser
from dissertation.models.dissertation_role import DissertationRole
from dissertation.models.offer_proposition import OfferProposition
from base import models as mdl
from dissertation.forms import AdviserForm, ManagerAdviserForm
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError
from django.db.models import Q
from operator import attrgetter


def is_manager(user):
    person = mdl.person.find_by_user(user)
    adviser = Adviser.find_by_person(person)
    return adviser.type == 'MGR'


@login_required
def informations(request):
    person = mdl.person.find_by_user(request.user)
    try:
        adviser = Adviser(person=person, available_by_email=False, available_by_phone=False, available_at_office=False)
        adviser.save()
    except IntegrityError:
        adviser = Adviser.find_by_person(person)

    return render(request, "informations.html", {'adviser': adviser})


@login_required
def informations_detail_list(request):
    person = mdl.person.find_by_user(request.user)
    try:
        adviser = Adviser(person=person, available_by_email=False, available_by_phone=False, available_at_office=False)
        adviser.save()
    except IntegrityError:
        adviser = Adviser.find_by_person(person)

    queryset = DissertationRole.objects.all()
    adviser_list_dissertations = queryset.filter(Q(status='PROMOTEUR') & Q(adviser__pk=adviser.pk) &
    Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
    Q(dissertation__status='ENDED') |Q(dissertation__status='DEFENDED'))
    return render(request, "informations_detail_list.html", {'adviser_list_dissertations': adviser_list_dissertations,
                                                             'adviser': adviser})


@login_required
def informations_detail_stats(request):
    person = mdl.person.find_by_user(request.user)
    try:
        adviser = Adviser(person=person, available_by_email=False, available_by_phone=False, available_at_office=False)
        adviser.save()
    except IntegrityError:
        adviser = Adviser.find_by_person(person)

    queryset = DissertationRole.objects.all()
    count_advisers = queryset.filter(Q(adviser=adviser) & Q(dissertation__active=True)).count()
    count_advisers_pro = queryset.filter(
        Q(adviser=adviser) & Q(status='PROMOTEUR') &
        Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
                                              Q(dissertation__status='ENDED') |
                                              Q(dissertation__status='DEFENDED')).count()

    count_advisers_pro_request = queryset.filter(
        Q(adviser=adviser) & Q(status='PROMOTEUR') &
        Q(dissertation__status='DIR_SUBMIT') & Q(dissertation__active=True)).count()

    advisers_copro = queryset.filter(
        Q(adviser=adviser) & Q(status='CO_PROMOTEUR') &
        Q(dissertation__active=True)).exclude(
        Q(dissertation__status='DRAFT') | Q(dissertation__status='ENDED') |
        Q(dissertation__status='DEFENDED'))
    count_advisers_copro = advisers_copro.count()
    tab_offer_count_copro = {}
    # iterates dissertation_role where adviser is co_promo exluding DRAFT-ENDED-DEFENDED dissertations
    for dissertaion_role_copro in advisers_copro:
        if dissertaion_role_copro.dissertation.offer_year_start.offer.title in tab_offer_count_copro:
            tab_offer_count_copro[dissertaion_role_copro.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_copro[str(dissertaion_role_copro.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_copro[dissertaion_role_copro.dissertation.offer_year_start.offer.title] = 1

    advisers_reader = queryset.filter(Q(adviser=adviser) &
                                      Q(status='READER') & Q(dissertation__active=True)).exclude(
        Q(dissertation__status='DRAFT') |
        Q(dissertation__status='ENDED') | Q(dissertation__status='DEFENDED'))
    count_advisers_reader = advisers_reader.count()
    tab_offer_count_read = {}
    for dissertaion_role_read in advisers_reader:
        if dissertaion_role_read.dissertation.offer_year_start.offer.title in tab_offer_count_read:
            tab_offer_count_read[dissertaion_role_read.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_read[str(dissertaion_role_read.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_read[dissertaion_role_read.dissertation.offer_year_start.offer.title] = 1

    advisers_pro = queryset.filter(Q(adviser=adviser) &
                                   Q(status='PROMOTEUR') &
                                   Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
                                                                         Q(dissertation__status='ENDED') |
                                                                         Q(dissertation__status='DEFENDED'))
    tab_offer_count_pro = {}
    for dissertaion_role_pro in advisers_pro:
        if dissertaion_role_pro.dissertation.offer_year_start.offer.title in tab_offer_count_pro:
            tab_offer_count_pro[dissertaion_role_pro.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_pro[str(dissertaion_role_pro.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_pro[dissertaion_role_pro.dissertation.offer_year_start.offer.title] = 1

    return render(request, 'informations_detail_stats.html',
                  {'adviser': adviser, 'count_advisers': count_advisers, 'count_advisers_copro': count_advisers_copro,
                   'count_advisers_pro': count_advisers_pro, 'count_advisers_reader': count_advisers_reader,
                   'count_advisers_pro_request': count_advisers_pro_request,
                   'tab_offer_count_pro': tab_offer_count_pro, 'tab_offer_count_read': tab_offer_count_read,
                   'tab_offer_count_copro': tab_offer_count_copro})


@login_required
def informations_edit(request):
    person = mdl.person.find_by_user(request.user)
    adviser = Adviser.find_by_person(person)
    if request.method == "POST":
        form = AdviserForm(request.POST, instance=adviser)
        if form.is_valid():
            adviser = form.save(commit=False)
            adviser.save()
            return redirect('informations')
    else:
        form = AdviserForm(instance=adviser)

    return render(request, "informations_edit.html", {'form': form, 'person': person})


@login_required
@user_passes_test(is_manager)
def manager_informations(request):
    advisers = Adviser.find_all().filter(type='PRF')
    return render(request, 'manager_informations_list.html', {'advisers': advisers})


@login_required
@user_passes_test(is_manager)
def manager_informations_detail(request, pk):
    adviser = get_object_or_404(Adviser, pk=pk)
    return render(request, 'manager_informations_detail.html', {'adviser': adviser})


@login_required
@user_passes_test(is_manager)
def manager_informations_edit(request, pk):
    adviser = get_object_or_404(Adviser, pk=pk)
    if request.method == "POST":
        form = ManagerAdviserForm(request.POST, instance=adviser)
        if form.is_valid():
            adviser = form.save(commit=False)
            adviser.save()
            return redirect('manager_informations_detail', pk=adviser.pk)
    else:
        form = AdviserForm(instance=adviser)

    return render(request, "manager_informations_edit.html", {'adviser': adviser, 'form': form})


@login_required
@user_passes_test(is_manager)
def manager_informations_search(request):
    advisers = Adviser.search(terms=request.GET['search'])
    return render(request, "manager_informations_list.html", {'advisers': advisers})


@login_required
@user_passes_test(is_manager)
def manager_informations_list_request(request):
    queryset = DissertationRole.objects.all()
    advisers_need_request = queryset.filter(Q(status='PROMOTEUR') &
                                            Q(dissertation__status='DIR_SUBMIT') &
                                            Q(dissertation__active=True))
    advisers_need_request = advisers_need_request.order_by('adviser')

    return render(request, "manager_informations_list_request.html", {'advisers_need_request': advisers_need_request})

@login_required
@user_passes_test(is_manager)
def manager_informations_detail_list(request, pk):
    adviser = get_object_or_404(Adviser, pk=pk)
    queryset = DissertationRole.objects.all()
    adviser_list_dissertations = queryset.filter(Q(status='PROMOTEUR') & Q(adviser__pk=pk) &
    Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
    Q(dissertation__status='ENDED') |Q(dissertation__status='DEFENDED'))
    return render(request, "manager_informations_detail_list.html", {'adviser_list_dissertations': adviser_list_dissertations,'adviser':adviser})


@login_required
@user_passes_test(is_manager)
def manager_informations_detail_stats(request, pk):
    adviser = get_object_or_404(Adviser, pk=pk)
    queryset = DissertationRole.objects.all()
    count_advisers = queryset.filter(Q(adviser=adviser) & Q(dissertation__active=True)).count()
    count_advisers_pro = queryset.filter(
        Q(adviser=adviser) & Q(status='PROMOTEUR') &
        Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
                                              Q(dissertation__status='ENDED') |
                                              Q(dissertation__status='DEFENDED')).count()

    count_advisers_pro_request = queryset.filter(
        Q(adviser=adviser) & Q(status='PROMOTEUR') &
        Q(dissertation__status='DIR_SUBMIT') & Q(dissertation__active=True)).count()

    advisers_copro = queryset.filter(
        Q(adviser=adviser) & Q(status='CO_PROMOTEUR') &
        Q(dissertation__active=True)).exclude(
        Q(dissertation__status='DRAFT') | Q(dissertation__status='ENDED') |
        Q(dissertation__status='DEFENDED'))
    count_advisers_copro = advisers_copro.count()
    tab_offer_count_copro = {}
    # iterates dissertation_role where adviser is co_promo exluding DRAFT-ENDED-DEFENDED dissertations
    for dissertaion_role_copro in advisers_copro:
        if dissertaion_role_copro.dissertation.offer_year_start.offer.title in tab_offer_count_copro:
            tab_offer_count_copro[dissertaion_role_copro.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_copro[str(dissertaion_role_copro.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_copro[dissertaion_role_copro.dissertation.offer_year_start.offer.title] = 1

    advisers_reader = queryset.filter(Q(adviser=adviser) &
                                      Q(status='READER') & Q(dissertation__active=True)).exclude(
        Q(dissertation__status='DRAFT') |
        Q(dissertation__status='ENDED') | Q(dissertation__status='DEFENDED'))
    count_advisers_reader = advisers_reader.count()
    tab_offer_count_read = {}
    for dissertaion_role_read in advisers_reader:
        if dissertaion_role_read.dissertation.offer_year_start.offer.title in tab_offer_count_read:
            tab_offer_count_read[dissertaion_role_read.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_read[str(dissertaion_role_read.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_read[dissertaion_role_read.dissertation.offer_year_start.offer.title] = 1

    advisers_pro = queryset.filter(Q(adviser=adviser) &
                                   Q(status='PROMOTEUR') &
                                   Q(dissertation__active=True)).exclude(Q(dissertation__status='DRAFT') |
                                                                         Q(dissertation__status='ENDED') |
                                                                         Q(dissertation__status='DEFENDED'))
    tab_offer_count_pro = {}
    for dissertaion_role_pro in advisers_pro:
        if dissertaion_role_pro.dissertation.offer_year_start.offer.title in tab_offer_count_pro:
            tab_offer_count_pro[dissertaion_role_pro.dissertation.offer_year_start.offer.title] = \
                tab_offer_count_pro[str(dissertaion_role_pro.dissertation.offer_year_start.offer.title)] + 1
        else:
            tab_offer_count_pro[dissertaion_role_pro.dissertation.offer_year_start.offer.title] = 1

    return render(request, 'manager_informations_detail_stats.html',
                  {'adviser': adviser, 'count_advisers': count_advisers, 'count_advisers_copro': count_advisers_copro,
                   'count_advisers_pro': count_advisers_pro, 'count_advisers_reader': count_advisers_reader,
                   'count_advisers_pro_request': count_advisers_pro_request,
                   'tab_offer_count_pro': tab_offer_count_pro, 'tab_offer_count_read': tab_offer_count_read,
                   'tab_offer_count_copro': tab_offer_count_copro})
