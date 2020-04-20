import logging
import os
import re
import uuid
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import (Http404, HttpResponse, HttpResponseNotFound,
                         JsonResponse)
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import (authentication, generics, mixins, permissions,
                            renderers, status, viewsets)
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from localResWS.ws import models
from localResWS.ws import serializers

LOCAL_DATA_DIR = os.path.join(settings.BASE_DIR, 'service/data')
VOLMAP_FILENAME = 'local_resol.vol'
logger = logging.getLogger(__name__)


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'categories': reverse('category-list', request=request, format=format),
        'types': reverse('type-list', request=request, format=format)
    })

class CategoryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.AnnCategory.objects.all()
    serializer_class = serializers.CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.AnnType.objects.all()
    serializer_class = serializers.TypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(category=self.request.user)

class EntryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.Entry.objects.all()
    serializer_class = serializers.EntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


#  ######################################################################

def getEntryFiles(entryId):
    entry = None
    # query by EMBD ID
    if re.search(r"^emd-\d{4,5}$", entryId):
        logger.debug("Get entry files for %s", entryId)
        entry = getEntryDatafiles(entryId)
    return entry

def getEntryDatafiles(entryId):
    path = os.path.join(LOCAL_DATA_DIR, entryId)
    data_files = []
    re_vol_file = re.compile('^local_resol\.vol$')
    re_pdb_file = re.compile('^pdb\d\w{3}\.ent$')
    re_LR_file = re.compile('^pdb\d\w{3}_LR_\w+\.pdb$')
    re_mapQ_file = re.compile('^pdb\d\w{3}_mapQ_\w+\.pdb$')
    
    try:
        dir_list = os.listdir(path)
        # new entry
        logger.debug('Creating new entry: %s', entryId)
        entry = models.Entry(entryId=entryId, path=path)
        
        for filename in dir_list:
            if re_vol_file.match(path):
                logger.debug('Found volume file %s', filename)
                data_files.append(filename)

            if re_pdb_file.match(path):
                logger.debug('Found pdb file %s', filename)
                data_files.append(filename)

            if re_LR_file.match(path):
                logger.debug('Found LR file %s', filename)
                data_files.append(filename)

            if re_mapQ_file.match(path):
                logger.debug('Found mapQ file %s', filename)
                data_files.append(filename)
        entry.data_files = data_files
        entry.save()
        return entry
    except:
        raise Exception

class EntryDetail(APIView):
    """
    Retrieve, update or delete an annotation entry.
    """
    def get(self, request, query_id, format=None):
        """
        Retrieve an annotation entry.
        """
        # get from DB
        try:
            entry = models.Entry.objects.get(entryId__iexact=query_id)
            logger.debug("Found %s in DB", query_id)
            serializer = serializers.EntrySerializer(entry)
            return Response(serializer.data)
        except (ValueError, ValidationError, models.Entry.DoesNotExist) as exc:
            # check from disk
            try:
                entry = getEntryFiles(query_id)
                logger.debug("Found %s in Disk", query_id)
                serializer = serializers.EntrySerializer(entry)
                return Response(serializer.data)
            except:
                return HttpResponseNotFound()


class DataFileViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
