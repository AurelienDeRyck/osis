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
from django.contrib.auth.decorators import login_required
from django.http import *
from django.shortcuts import get_object_or_404, render, redirect
from dissertation import models as mdl
from dissertation.models.enums import document_type
from osis_common import models as mdl_osis_common
from osis_common.forms import UploadDocumentFileForm
from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer


@login_required
def download(request, pk):
    proposition_document = mdl.proposition_document_file.find_by_id(pk)
    document = mdl_osis_common.document_file.find_by_id(proposition_document.document_file.id)
    filename = document.file_name
    response = HttpResponse(document.file, content_type=document.content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@login_required
def upload_file_description(request):
    """
    To display the scree to upload id_picture
    :param request:
    :return:
    """
    description = request.POST['description']
    proposition_id = request.POST['proposition_dissertation_id']
    if not proposition_id.isdigit():
        proposition_id = None
    documents = mdl_osis_common.document_file.search(user=request.user, description=description)
    form = UploadDocumentFileForm(initial={'storage_duration': 0,
                                           'document_type': "dissertation",
                                           'user': request.user})
    if proposition_id:
        proposition = mdl.proposition_dissertation.find_by_id(proposition_id)
    else:
        proposition = None
    return render(request, 'new_document.html', {
        'form': form,
        'content_type_choices': mdl_osis_common.document_file.CONTENT_TYPE_CHOICES,
        'description_choices': mdl.enums.document_type.DOCUMENT_TYPE_CHOICES,
        'description': description,
        'documents': documents,
        'proposition_dissertation': proposition})


@login_required
def upload_document(request):
    documents = mdl_osis_common.document_file.search(user=request.user, description=None)
    if request.method == "POST":
        description = None
        if request.POST['description']:
            description = request.POST['description']
        form = UploadDocumentFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save()
            file.size = file.file.size
            file.file_name = request.FILES['file'].name
            file_type = form.cleaned_data["file"]
            content_type = file_type.content_type
            file.content_type = content_type
            file.save()
            return redirect('new_document')
        else:
            if description == mdl.enums.document_type.DOCUMENT_TYPE_CHOICES[document_type.ID_PICTURE]:
                # return common.home(request)
                return HttpResponseRedirect(reverse('home', ))
            else:
                return render(request, 'new_document.html', {
                    'form': form,
                    'content_type_choices': mdl_osis_common.document_file.CONTENT_TYPE_CHOICES,
                    'description_choices': mdl.enums.document_type.DOCUMENT_TYPE_CHOICES,
                    'description': description,
                    'documents': documents})


@login_required
def delete_old(request, pk):
    document = get_object_or_404(mdl_osis_common.document_file.DocumentFile, pk=pk)
    if document:
        description = document.description
        document.delete()
        documents = mdl_osis_common.document_file.search(user=request.user, description=description)
        return render(request, 'new_document.html', {
            'content_type_choices': mdl_osis_common.document_file.CONTENT_TYPE_CHOICES,
            'description_choices': mdl.enums.document_type.DOCUMENT_TYPE_CHOICES,
            'description': description,
            'documents': documents})


def save_document_from_form(document, request):
    """
    Save a document (attachment) from a form.
    :param document: an UploadDocumentForm received from a POST request.
    :param request:
    :return:
    """
    file_name = request.FILES['file'].name
    file = document.cleaned_data['file']
    description = document.cleaned_data['description']
    # Never trust a user. They could change the hidden input values.
    # Ex: user, document_type, storage_duration, etc.
    storage_duration = 0
    content_type = file.content_type
    size = file.size
    doc_file = mdl_osis_common.document_file.DocumentFile(file_name=file_name,
                                                          file=file,
                                                          description=description,
                                                          storage_duration=storage_duration,
                                                          application_name='dissertation',
                                                          content_type=content_type,
                                                          size=size,
                                                          user=request.user)
    doc_file.save()


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = mdl_osis_common.document_file.DocumentFile
        fields = ('id', 'file_name', 'file')


def find_by_description(request):
    description = request.GET['description']
    documents = mdl_osis_common.document_file.search(request.user, description)
    last_documents = []
    if documents:
        last_document = documents.reverse()[0]
        last_documents = [last_document]
    serializer = DocumentFileSerializer(last_documents, many=True)
    return JSONResponse(serializer.data)


def save_uploaded_file(request):
    data = request.POST
    if request.method == 'POST':
        if request.POST.get('proposition_dissertation_id'):
            proposition = mdl.proposition_dissertation.find_by_id(request.POST['proposition_dissertation_id'])
        file_selected = request.FILES['file']
        file_s = file_selected
        file_name = file_selected.name
        content_type = file_selected.content_type
        size = file_selected.size
        description = data['description']
        storage_duration = 0
        documents = mdl.proposition_document_file.search(proposition, description)
        for document in documents:
            document.delete()
        documents = mdl_osis_common.document_file.search(user=request.user, description=description)
        for document in documents:
            document.delete()
        doc_file = mdl_osis_common.document_file.DocumentFile(file_name=file_name,
                                                              file=file_s,
                                                              description=description,
                                                              storage_duration=storage_duration,
                                                              application_name='dissertation',
                                                              content_type=content_type,
                                                              size=size,
                                                              user=request.user)
        doc_file.save()
        adm_doc_file = mdl.proposition_document_file.PropositionDocumentFile()
        adm_doc_file.proposition = proposition
        adm_doc_file.document_file = doc_file
        adm_doc_file.save()
    return HttpResponse('')


@login_required
def delete_document_file(request):
    pk = request.POST.get('document_file_id')
    if pk:
        document = get_object_or_404(mdl_osis_common.document_file.DocumentFile, pk=pk)
        if document:
            document.delete()
    else:
        description = request.POST.get('description')
        document = mdl_osis_common.document_file.search(request.user, description)
        if document:
            document_applicant_list = mdl.proposition_document_file.find_by_document(document)
            if document_applicant_list.exists():
                for document_applicant in document_applicant_list:
                    document_applicant.delete()
            document.delete()
    return HttpResponse('')
