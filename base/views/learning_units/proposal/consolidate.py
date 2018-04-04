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
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

from base.business.learning_unit_proposal import consolidate_creation_proposal
from base.models.enums.proposal_state import ProposalState
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.common import display_success_messages, display_error_messages


@login_required
@require_POST
@permission_required('base.can_consolidate_learningunit_proposal', raise_exception=True)
def consolidate_proposal(request):
    learning_unit_year_id = request.POST.get("learning_unit_year_id")
    proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year__id=learning_unit_year_id)
    eligible_states = (ProposalState.ACCEPTED.name, ProposalState.REFUSED.name)
    if proposal.state not in eligible_states:
        raise PermissionDenied("Proposal learning unit is neither accepted nor refused.")

    try:
        result = consolidate_creation_proposal(proposal)
        display_success_messages(request, result, extra_tags='safe')
    except IntegrityError as e:
        display_error_messages(request, e.args[0])

    return redirect('learning_unit', learning_unit_year_id=learning_unit_year_id)
