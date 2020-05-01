import logging
import os
import re
import uuid
from wsgiref.util import FileWrapper

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from rest_framework import (permissions,
                            status, viewsets)
from rest_framework.response import Response
from rest_framework.views import APIView

from localResWS.ws import models, serializers
from localResWS.ws.dataPaths import LOCAL_DATA_DIR
from localResWS.ws.models import FILE_TYPES, ENTRY_TYPES
from localResWS.ws.utils import updateDB_modifiedPdbs, updateDB_annoFromMaps, getEntryAnnFromMapsFiles, \
    PdbEntryAnnFromMapsUtils

logger = logging.getLogger(__name__)

REGEX_PDB_ID = re.compile('^\d\w{3}$')


DEEP_RES_FNAME_TEMPLATE="%(pdb_id)s.deepres.aa.pdb"
MONORES_FNAME_TEMPLATE="%(pdb_id)s.monores.aa.pdb"
MAPQ_FNAME_TEMPLATE="%(pdb_id)s.mapq.aa.pdb"
ANN_TYPES_DICT={"localResolution":{"deepres":DEEP_RES_FNAME_TEMPLATE, "monores":MONORES_FNAME_TEMPLATE}, "modelQuality":{"mapq":MAPQ_FNAME_TEMPLATE}}
ANN_TYPES_MIN_VAL={"localResolution":{"deepres":1.5, "monores":1.5}, "modelQuality":{"mapq":-1}}



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
    entry_list=[]
    entry_list+=updateDB_annoFromMaps()
    entry_list+= updateDB_modifiedPdbs("isolde")
    entry_list+= updateDB_modifiedPdbs("pdb-redo")

    return entry_list


class EntryAnnFromMapsView(APIView):
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
                entry = getEntryAnnFromMapsFiles(query_id)
                if entry:
                    serializer = serializers.EntrySerializer(entry)
                    return Response(serializer.data)
                else:
                    return not_found_resp(query_id)
            except:
                logger.exception(exc)
                return not_found_resp(query_id)


class PdbEntryFakeView(APIView):
    """
    Retrieve an annotation entry `details`.
    """
    def get(self, request, pdb_id, chain_id, format=None):
        """
        Get fake data json for pdb_id, chain_id
        """
        import random
        fakeJson=[ {"chain":chain_id, "data": [ {"begin":str(i), "value":2+5*random.random()} for i in range(1,250) ] }]
        return Response(fakeJson)


class PdbEntryAllAnnFromMapView(APIView, PdbEntryAnnFromMapsUtils):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, pdb_id, chain_id, format=None):
        """
        Get all map derived annotations related to one pdb_id, chain_id
        """

        pdb_id= pdb_id.lower()
        if not re.search(REGEX_PDB_ID, pdb_id):
            logger.debug("Bad Request Entry ID: %s", pdb_id)
            content = { "request":pdb_id, 
                        "detail": "entryId _strictly_ must be in the form `####/#`" }

            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        responseData=[]

        for algFamily in ANN_TYPES_DICT:
          for algoName in ANN_TYPES_DICT[algFamily]:
            modifiedPdbFname=  ANN_TYPES_DICT[algFamily][algoName]%{"pdb_id":pdb_id}
            modifiedPdbFname= self._locateFname(modifiedPdbFname)
            if modifiedPdbFname is not None:
                algoDataDict= self._getJsonFromFname(modifiedPdbFname, chain_id, minToFilter= ANN_TYPES_MIN_VAL[algFamily][algoName] )
                if algoDataDict is not None:
                    algoDataDict["algorithm"]=algoName
                    algoDataDict["algoType"]=algFamily
                    responseData.append(algoDataDict)

        if len(responseData)==0:
          logger.debug("Not found %s", pdb_id+"/"+chain_id)
          return not_found_resp(pdb_id)

        return Response(responseData)


class DownloadGenericFile(APIView):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, file_uuid, format=None):
        """
        downloads a generic file given its uuid
        """
        try:
            logger.debug("Trying to identify file %s" % str(file_uuid))
            fileRecord= models.DataFile.objects.get(unique_id=uuid.UUID(file_uuid))
        except (ValueError, ValidationError, models.DataFile.DoesNotExist) as exc:
            logger.debug("Error not found: %s" % file_uuid)
            return HttpResponseNotFound()

        fullName= os.path.join(fileRecord.path, fileRecord.filename)
        logger.debug("Trying to download %s"%fullName)
        with open(fullName, "rb") as fileObj:
            response = HttpResponse(FileWrapper(fileObj),
                                    content_type='application/x-gzip')
            response['Content-Disposition'] = 'attachment; filename="%s"' % fileRecord.filename
            return response


class ListModifiedPDBView(APIView):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, model_type, pdb_id, format=None):
        """
        Provide downloading links for modified pdbs
        """
        pdb_id = pdb_id.lower()
        try:
            fileRecords = models.DataFile.objects.filter(entry__entryId=pdb_id, entry__entryType=ENTRY_TYPES[1],
                                                     fileType__iexact=FILE_TYPES[1], method=model_type)
        except (ValueError, ValidationError, models.DataFile.DoesNotExist) as exc:
            #TODO: try to find files locally using findPdbRedo / findIsolde and create the database entry before error.
            return not_found_resp(model_type+"/"+model_type)

        logger.debug(fileRecords)
        responseData={}
        for record in fileRecords:
            url= "files/modifiedPdb/download/%s"%record.unique_id
            responseData[record.filename]= url
        if len(responseData)==0:
          logger.debug("Not found %s", pdb_id+"/"+model_type)
          return not_found_resp(pdb_id+"/"+model_type)
        return Response(responseData)

class EntryListUpdateView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    # def post(self, request, format=None):
    def get(self, request, format=None):
        logger.debug("Updating DB from data folder: %s", LOCAL_DATA_DIR)
        entry_list = update_DB_from_Disk()
        if entry_list:
            logger.debug("...got some new entries: %d", len(entry_list))
            return Response({ "request": "DB update","detail": "Got some new entries: "+str(len(entry_list))}, status=status.HTTP_201_CREATED)
        else:
            return Response({"request": "DB update","detail":"No new entries found."}, status=status.HTTP_204_NO_CONTENT)
