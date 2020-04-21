import logging
import os
import re
import uuid
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import (authentication, generics, mixins, permissions,
                            renderers, status, viewsets)
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from localResWS.ws import models, serializers


logger = logging.getLogger(__name__)
LOCAL_DATA_DIR = os.path.join(settings.BASE_DIR, 'service/data')
REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile('^local_resol\.vol$')
REGEX_PDB_FILE = re.compile('^pdb\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^pdb\d\w{3}_LR_\w+\.pdb$')
REGEX_MAPQ_FILE = re.compile('^pdb\d\w{3}_mapQ_\w+\.pdb$')


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

class DataFileViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.DataFile.objects.all()
    serializer_class = serializers.DataFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class DataSetViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.DataSet.objects.all()
    serializer_class = serializers.DataSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


#  ######################################################################

def not_found_resp(query_id):
    logger.debug("Not found %s", query_id)
    content = { "request":query_id, 
                "detail": "Annotation Entry Not Found" }
    return Response(content, status=status.HTTP_404_NOT_FOUND)

def bad_entry_request(query_id):
    logger.debug("Bad Request Entry ID: %s", query_id)
    content = { "request":query_id, 
                "detail": "entryId _strictly_ must be in the form `emd-#####`" }
    return Response(content, status=status.HTTP_400_BAD_REQUEST)

def update_DB_from_Disk():
    logger.debug("Update DB from data folder: %s", LOCAL_DATA_DIR)
    path = os.path.join(LOCAL_DATA_DIR)
    reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAPQ_FILE]
    entry_list = []
    try:
        dir_names = [ f.name for f in os.scandir(LOCAL_DATA_DIR) if f.is_dir() and REGEX_EMDB_ID.match(f.name) ]
        for dir_name in dir_names:
            # check if entry already exists
            try:
                models.Entry.objects.get(entryId__iexact=dir_name)
            except (models.Entry.DoesNotExist) as exc:
                # logger.exception(exc)
                # new entry
                logger.debug('Creating new entry: %s from %s', dir_name, path)
                entry = models.Entry(entryId=dir_name, path=path)
                entry.save()
                # find files inside
                logger.debug('Searching for datafiles: %s ', dir_name)
                dir_list = os.listdir(os.path.join(path, dir_name))
                for filename in dir_list:
                    for reg_exp in reg_expressions:
                        if reg_exp.match(filename):
                            logger.debug('Found data file %s', filename)
                            logger.debug('Creating new dataFile %s record', filename)
                            data_file = models.DataFile(filename=filename, path=path, entry=entry)
                            data_file.save()
                entry_list.append(entry)
        return entry_list
    except() as exc:
        logger.exception(exc)
    return

def getEntryFiles(entryId):
    logger.debug("Get entry files for %s", entryId)
    path = os.path.join(LOCAL_DATA_DIR, entryId)
    reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAPQ_FILE]
    try:
        dir_list = os.listdir(path)
        # new entry
        logger.debug('Creating new entry: %s from %s', entryId, path)
        entry = models.Entry(entryId=entryId, path=path)
        entry.save()
        for filename in dir_list:
            for reg_exp in reg_expressions:
                if reg_exp.match(filename):
                    logger.debug('Found data file %s', filename)
                    logger.debug('Creating new dataFile %s record', filename)
                    data_file = models.DataFile(filename=filename, path=path, entry=entry)
                    data_file.save()
        return entry
    except() as exc:
        logger.exception(exc)

class EntryDetailView(APIView):
    """
    Retrieve an annotation entry `details`.
    """
    def get(self, request, query_id, format=None):
        """
        Get `details` for an annotation entry.
        """
        if not re.search(r"^emd-\d{4,5}$", query_id):
            return bad_entry_request(query_id)
        # get from DB
        try:
            logger.debug("Searching %s in DB", query_id)
            entry = models.Entry.objects.get(entryId__iexact=query_id)
            if entry:
                serializer = serializers.EntrySerializer(entry)
                return Response(serializer.data)
            else:
                logger.debug("Not found %s in DB", query_id)
                return not_found_resp(query_id)
        except (ValueError, ValidationError, models.Entry.DoesNotExist) as exc:
            logger.exception(exc)
            # check from disk
            try:
                logger.debug("Searching %s in Disk", query_id)
                entry = getEntryFiles(query_id)
                if entry:
                    serializer = serializers.EntrySerializer(entry)
                    return Response(serializer.data)
                else:
                    return not_found_resp(query_id)
            except:
                logger.exception(exc)
                return not_found_resp(query_id)


class EntryListUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # def post(self, request, format=None):
    def get(self, request, format=None):
        logger.debug("Updating DB from data folder: %s", LOCAL_DATA_DIR)
        entry_list = update_DB_from_Disk()
        if entry_list:
            logger.debug("...got some new entries: %d", len(entry_list))
            return Response({ "request": "DB update","detail": "Got some new entries: "+str(len(entry_list))}, status=status.HTTP_201_CREATED)
        else:
            return Response({"request": "DB update","detail":"No new entries found."}, status=status.HTTP_204_NO_CONTENT)
