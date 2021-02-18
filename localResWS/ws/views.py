import logging
import os
import re
import uuid
from wsgiref.util import FileWrapper

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import FilterSet, ModelChoiceFilter
from django_filters import rest_framework as filters
from localResWS.ws import models, serializers
from localResWS.ws.dataPaths import (COMPUT_MODELS_DIR, LOCAL_DATA_DIR,
                                     MODEL_AND_LIGAND_DIR,
                                     EMV_WS_URL,
                                     EMV_WS_PATH)
from localResWS.ws.models import ENTRY_TYPES, FILE_TYPES
from localResWS.ws.utils import (PdbEntryAnnFromMapsUtils,
                                 getEntryAnnFromMapsFiles,
                                 updateDB_annoFromMaps,
                                 updateDB_modelAndLigand,
                                 updateDB_modifiedPdbs)                  
import requests                           


logger = logging.getLogger(__name__)

REGEX_PDB_ID = re.compile('^\d\w{3}$')


DEEP_RES_FNAME_TEMPLATE="%(pdb_id)s.deepres.aa.pdb"
MONORES_FNAME_TEMPLATE="%(pdb_id)s.monores.aa.pdb"
MAPQ_FNAME_TEMPLATE="%(pdb_id)s.mapq.aa.pdb"
FSCQ_TEMPLATE= "%(pdb_id)s.fscq.aa.pdb"
ANN_TYPES_DICT={"localResolution":{"deepres":DEEP_RES_FNAME_TEMPLATE, "monores":MONORES_FNAME_TEMPLATE}, "modelQuality":{"mapq":MAPQ_FNAME_TEMPLATE, "fscq":FSCQ_TEMPLATE}}
ANN_TYPES_MIN_VAL={"localResolution":{"deepres":1.5, "monores":1.5}, "modelQuality":{"mapq":-1, "fscq":-3}}



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

    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['unique_id', 'filename', 'path', 'fileType', 'method']
    ordering_fields = ['entry__entryId', 'unique_id', 'filename', 'path' , 'fileType', 'method']
    ordering = ['entry__entryId', 'path', 'filename']


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

def update_DB_from_Disk(): #TODO: launnch a thread so that you dont get timeout
    logger.debug("Update DB from data folder: %s", LOCAL_DATA_DIR)
    entry_list=[]
    entry_list+=updateDB_annoFromMaps()
    entry_list+= updateDB_modifiedPdbs("isolde")
    entry_list+= updateDB_modifiedPdbs("pdb-redo")
    entry_list+= updateDB_modelAndLigand("covid19_COSS")
    print("Database updated")

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

    def get(self, request, pdb_id, chain_id, modified_model=None, format=None):
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
        if modified_model is not None:
            pdb_id=pdb_id+"."+modified_model
        for algFamily in ANN_TYPES_DICT:
          for algoName in ANN_TYPES_DICT[algFamily]:
            modifiedPdbFname=  ANN_TYPES_DICT[algFamily][algoName]%{"pdb_id":pdb_id}
            modifiedPdbFname= self._locateFname(modifiedPdbFname, modifiedPdbType=modified_model)
            if modifiedPdbFname is not None:
                algoDataDict= self._getJsonFromFname(modifiedPdbFname, chain_id, minToFilter= ANN_TYPES_MIN_VAL[algFamily][algoName] )
                if algoDataDict is not None:
                    algoDataDict["algorithm"]=algoName
                    algoDataDict["algoType"]=algFamily
                    responseData.append(algoDataDict)


        if len(responseData)==0:
            logger.debug("Not found %s", pdb_id+"/"+chain_id)
        #   Request EMV WebService to calculate the EMV scores
        #   This is an asyncronous call for computation. User must query again in the future to get results
            q_path = EMV_WS_URL +"/"+ EMV_WS_PATH +"/"+ pdb_id +"/"+ chain_id +"/"
            logger.debug("Requesting EMV WebService to calculate the EMV scores %s", q_path)
            try:
                headers = {'accept': 'application/json'}
                resp = requests.get(q_path, headers=headers, timeout=(2, 5))
                
                logger.debug("EMV WS-query: %s", resp.url)
                logger.debug("WS-response: %s, %s", resp.status_code, resp.json())
                if resp:
                    dresp = HttpResponse(
                        content=resp.content,
                        status=resp.status_code,
                        content_type=resp.headers['Content-Type']
)
                    return dresp
            except Exception as exc:
                logger.exception(exc)
            
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
        # logger.debug("Trying to download %s"%fullName)
        print("Trying to download %s"%fullName)
        with open(fullName, "rb") as fileObj:
            response = HttpResponse(FileWrapper(fileObj),
                                    content_type='application/x-gzip')
            response['Content-Disposition'] = 'attachment; filename="%s"' % fileRecord.filename
            return response


class ListModifiedPDBView(APIView):
    """
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
            return not_found_resp(model_type+"/"+pdb_id)

        logger.debug(fileRecords)
        responseData={}
        for record in fileRecords:
            url= "files/modifiedPdb/download/%s"%record.unique_id
            responseData[record.filename]= url
        if len(responseData)==0:
          logger.debug("Not found %s", pdb_id+"/"+model_type)
          return not_found_resp(pdb_id+"/"+model_type)
        return Response(responseData)


class ListModelsAbstract():
    def _processFname(self, fname, filters=None):
        if fname.endswith(".csv"):
            import pandas as pd
            data = pd.read_csv(fname)
            # print(data)
            if filters is not None:
                for filterId, filterValue in filters.items():
                    data = data[data[filterId] == filterValue]
            if data.shape[0] > 0:
                if data.shape[0] == 1:
                    return [data.to_dict(orient="records")]
                else:
                    return data.to_dict(orient="records")
            else:
                return None
        return None

class ListComputationalModelsView(APIView, ListModelsAbstract):
    """
    """

    def get(self, request, model_type, uniprot_id, prot_name=None, model_name=None, format=None):
        """
        Provide downloading links for modified pdbs
        """
        # print(uniprot_id, prot_name, model_name)

        filters = {"Uniprot_ID": uniprot_id.upper()}
        if prot_name is not None:
            filters.update({"Protein_ID": prot_name.upper()})
        if model_name is not None:
            filters.update({"model_name": model_name})
        print("Filters:", filters)
        responseData=[]
        for modelType in os.listdir(COMPUT_MODELS_DIR):
            if modelType==model_type:
                for fname in os.listdir(os.path.join(COMPUT_MODELS_DIR, modelType)):
                    dataJson= self._processFname(os.path.join(COMPUT_MODELS_DIR, modelType,fname), filters=filters)
                    if dataJson is not None:
                        responseData+= dataJson

        if len(responseData) == 0:
            logger.debug("Not found %s", uniprot_id + "/" + model_type)
            return not_found_resp(uniprot_id + "/" + model_type)
        return Response(responseData)

class DownloadComputationalModelsView(APIView, ListModelsAbstract):
    
    def get(self, request, model_type, model_name):
        """
        Downloads a generic file given its <model_type>/<model_name>
        """
        ext = ".pdb"
        responseData=[]
        for fname in os.listdir(os.path.join(COMPUT_MODELS_DIR, model_type)):
            if fname == model_name+ext:
                fullName= os.path.join(COMPUT_MODELS_DIR, model_type, fname)
                logger.debug("Trying to download %s"%fullName)
                # assuming *.pdb file is text
                with open(fullName, "r") as fileObj:
                    response = HttpResponse(
                        FileWrapper(fileObj),
                        content_type='text/plain')
                    response['Content-Disposition'] = 'attachment; filename="%s"' % fname
                    return response

        if len(responseData) == 0:
            logger.debug("File not found %s", model_name)
            return Response("File not found :" + model_name, status=status.HTTP_404_NOT_FOUND)
        return Response(responseData)


class DownloadModifiedPdbFile(APIView, ListModelsAbstract):
    
    def get(self, request, model_type, model_name):
        """
        downloads a generic file given its <model_type>/<model_name>
        """
        ext = ".pdb"
        model_name = model_name+ext
        try:
            logger.debug("Trying to identify file %s / %s " % (model_type, model_name))
            fileRecord= models.DataFile.objects.get(filename=model_name)
        except (ValueError, models.DataFile.DoesNotExist) as exc:
            logger.debug("Error not found: %s / %s" % (model_type, model_name))
            return HttpResponseNotFound()

        fullName= os.path.join(fileRecord.path, fileRecord.filename)
        # logger.debug("Trying to download %s"%fullName)
        print("Trying to download %s"%fullName)
        # assuming *.pdb file is text
        with open(fullName, "r") as fileObj:
            response = HttpResponse(
                FileWrapper(fileObj),
                content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="%s"' % fileRecord.filename
            return response


class ListPdbAndLigandView(APIView, ListModelsAbstract):
    """
    """


    def get(self, request, experiment_name, pdb_id=None, compound_id=None, pocket_id=None, pose_id=None, format=None):
        """
        Provide downloading links for modified pdbs
        """
        responseData = []
        if pocket_id is not None and pdb_id!="any" and pose_id is not None: #Fast access
            try:
                if experiment_name=="covid19_COSS":
                    filename = pdb_id+"_"+compound_id+"_"+pocket_id+"_"+pose_id+".pdb"
                    fileRecords = models.DataFile.objects.filter(entry__entryId=pdb_id, entry__entryType=ENTRY_TYPES[3], filename__iexact=filename,
                                                         fileType__iexact=FILE_TYPES[3], method=experiment_name)
                    responseData = {}
                    for record in fileRecords:
                        responseData["URL"] =  "files/genericDownload/%s" % record.unique_id
                        responseData["PDB_ID"] = pdb_id
                        responseData["compoundCode"] = compound_id
                        responseData["Pocket"]=pocket_id
                        responseData["Pose"]=pose_id
                        responseData["LibraryName"]="ZINC"
                    if len(responseData) >0:
                        return Response( [responseData] )

            except (ValueError, ValidationError, models.DataFile.DoesNotExist) as exc:
                return not_found_resp(experiment_name+"/"+str(pdb_id))
        #else
        filters={}
        if pdb_id is not None and pdb_id!="any":
            filters = {"PDB_ID": pdb_id.upper()}
        if compound_id is not None:
            filters.update({"compoundCode": compound_id})
        if pocket_id is not None:
            filters.update({"Pocket": pocket_id})
        if pose_id is not None:
            filters.update({"Pose": pose_id})
        print("Filters:", filters)
        for experimentName in os.listdir(MODEL_AND_LIGAND_DIR):
            if experimentName == experiment_name:
                for fname in os.listdir(os.path.join(MODEL_AND_LIGAND_DIR, experimentName)):
                    dataJson = self._processFname(os.path.join(MODEL_AND_LIGAND_DIR, experimentName, fname), filters=filters)
                    if dataJson is not None:
                        if isinstance(dataJson, list):
                            responseData += dataJson
                        else:
                            responseData.append( dataJson )

        if len(responseData) == 0:
            logger.debug("Not found %s", experiment_name + "/" + pdb_id)
            return not_found_resp(experiment_name + "/" + pdb_id)
        return Response(responseData)


class DownloadModelAndLigand(APIView, ListModelsAbstract):
    """
    """

    def get(self, request, experiment_name, pdb_id, compound_id, pocket_id, pose_id="1", format=None):
        pdb_id= pdb_id.upper()
        if experiment_name=="covid19_COSS":
            filename = pdb_id+"_"+compound_id+"_"+pocket_id+"_"+pose_id+".pdb"
            fullName= os.path.join( MODEL_AND_LIGAND_DIR, experiment_name, pdb_id, filename)
            print("fullName", fullName)
            if os.path.isfile(fullName):
                with open(fullName, "rb") as fileObj:
                    response = HttpResponse(FileWrapper(fileObj),
                                            content_type='application/x-gzip')
                    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
                    return response
        return not_found_resp(experiment_name+"/"+str(pdb_id))


#  ######################################################################
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


class UniprotEntryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.UniprotEntry.objects.all()
    serializer_class = serializers.UniprotEntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TrackTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.TrackType.objects.all()
    serializer_class = serializers.TrackTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FeatureTracksViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.FeatureTrack.objects.all()
    serializer_class = serializers.FeatureTrackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['uniprot_entry__accession', 'track_type__name', 'name']
    ordering_fields = ['name', 'track_type__name', 'uniprot_entry__accession']
    ordering = ['name', 'uniprot_entry__accession']

class TrackDataViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = models.TrackData.objects.all()
    serializer_class = serializers.FeatureDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['f_track__name', 'mutationType', 'mutationEffect']
    ordering_fields = ['f_track', 'begin', 'end', 'mutationType', 'mutationEffect']
    ordering = ['f_track']

class FeatureTrackDetailView(generics.ListAPIView):
    """
    Detail View for a given FeatureTrack
    """
    serializer_class = serializers.TrackDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_url_kwarg = 'acc'

    def get_queryset(self):
        """
        This view should return a FeatureTrack by UniProt and name
         Example:
            /featureTracks/<ACC>/<name>/
            /featureTracks/P0DTC4/Genomic_Variants_CNCB/
        """
        uniprot_acc = self.kwargs['acc']
        name = self.kwargs['name']
        return models.FeatureTrack.objects.filter(
            uniprot_entry__accession=uniprot_acc,
            name=name)

class TrackDetailView(generics.RetrieveAPIView):
    """
    Detail View for a given FeatureTrack
    """
    queryset = models.FeatureTrack.objects.all()
    serializer_class = serializers.TrackDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['mutationType', 'sourceType', 'mutationEffect']
    search_fields = ['mutationType']
    ordering_fields = ['mutationType', 'mutationEffect', 'sourceType']
    ordering = ['mutationType']
    lookup_url_kwarg = 'name'
    multiple_lookup_fields = ['uniprot_entry', 'name']
    
    def get_object(self):
        queryset = self.get_queryset()
        filter = {}
        for field in self.multiple_lookup_fields:
            filter[field] = self.kwargs[field]

        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj
