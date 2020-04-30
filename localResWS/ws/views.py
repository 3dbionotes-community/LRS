import logging
import os
import re

from django.core.exceptions import ValidationError
from rest_framework import (permissions,
                            status, viewsets)
from rest_framework.response import Response
from rest_framework.views import APIView

from localResWS.ws import models, serializers
from localResWS.ws.dataPaths import LOCAL_DATA_DIR, EMDB_BASEDIR, EMDB_DATA_DIR, THORN_DATA_DIR
from localResWS.ws.models import FILE_TYPES, ENTRY_TYPES
from localResWS.ws.utils import findIsolde

logger = logging.getLogger(__name__)
REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_PDB_ID = re.compile('^\d\w{3}$')
REGEX_VOL_FILE = re.compile('^emd-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile('^pdb\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAPQ_FILE = re.compile('^\d\w{3}\.mapq\.pdb$')

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
    reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAPQ_FILE]
    entry_list = []
    path = os.path.join(LOCAL_DATA_DIR, EMDB_BASEDIR)
    try:
        dir_names = [ f.name for f in os.scandir(path) if f.is_dir() and REGEX_EMDB_ID.match(f.name) ]
        for dir_name in dir_names:
            # check if entry already exists
            try:
                models.Entry.objects.get(entryId__iexact=dir_name, entryType__iexact=ENTRY_TYPES[0])
            except (models.Entry.DoesNotExist) as exc:
                # logger.exception(exc)
                # new entry
                logger.debug('Creating new entry: %s from %s', dir_name, path)
                entry = models.Entry(entryId=dir_name, path=path, entryType=ENTRY_TYPES[1])
                entry.save()
                # find files inside
                logger.debug('Searching for datafiles: %s ', dir_name)
                dir_list = os.listdir(os.path.join(path, dir_name))
                for filename in dir_list:
                    for reg_exp in reg_expressions:
                        if reg_exp.match(filename):
                            logger.debug('Found data file %s', filename)
                            logger.debug('Creating new dataFile %s record', filename)
                            data_file = models.DataFile(filename=filename, path=path, entry=entry, fileType=FILE_TYPES[0])
                            data_file.save()
                entry_list.append(entry)
    except() as exc:
        logger.exception(exc)

    for pdbId, listOfFnames in findIsolde().items():
        try:
            models.Entry.objects.get(entryId__iexact=pdbId, entryType__iexact=ENTRY_TYPES[1])
        except (models.Entry.DoesNotExist) as exc:
            # logger.exception(exc)
            # new entry
            logger.debug('Creating new isolde entry: %s', pdbId)
            entry = models.Entry(entryId=pdbId, path=THORN_DATA_DIR, entryType=ENTRY_TYPES[1])
            entry.save()
            # find files inside
            for filename in listOfFnames:
                logger.debug('Creating new dataFile %s record', filename)
                data_file = models.DataFile(filename=os.path.basename(filename), path=os.path.split(filename)[0], entry=entry, fileType=FILE_TYPES[1])
                data_file.save()
            entry_list.append(entry)

    return entry_list


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


class PdbEntryLocResUtils(object):


    def _getJsonFromFname(self, fneme, chain_id, minToFilter=-1):
      residues=[]
      values= []
      with open(fneme) as f:
        for line in f:
          if not "CA" in line or not "ATOM" in line: continue
          chainId= line[21]
          if chainId!=chain_id: continue
          resId= line[22:26].strip()
          bFactor=  float(line[54:60].strip())
          residues.append( {"begin":resId, "value":bFactor} )
          values.append(bFactor)
      if len(residues)==0:
        return None
      return {"chain":chain_id, "data":residues, "minVal": min([val for val in values if val > minToFilter]), "maxVal": max(values) }

    def _locateFname(self, targetFname):
      try:
          logger.debug("Searching %s in DB", targetFname)
          fileRecord = models.DataFile.objects.get(filename__iexact= targetFname, fileType__iexact=ENTRY_TYPES[0])
          if fileRecord:
            return os.path.join(fileRecord.path, fileRecord.filename)
          else:
              logger.debug("Not found %s in DB", targetFname)
              return None
      except (ValueError, ValidationError, models.DataFile.DoesNotExist) as exc:
          logger.exception(exc)
          # check from disk
          logger.debug("Searching %s in Disk", targetFname)

          for dirName in os.listdir(EMDB_DATA_DIR):
            for fname in os.listdir(os.path.join(EMDB_DATA_DIR, dirName)):
                if fname== targetFname:
                    return os.path.join(EMDB_DATA_DIR, dirName, fname)
      return None




class PdbEntryAllAnnAlgorithm(APIView, PdbEntryLocResUtils):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, pdb_id, chain_id, format=None):
        """
        Get fake data json for pdb_id, chain_id
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
            pdbFname=  ANN_TYPES_DICT[algFamily][algoName]%{"pdb_id":pdb_id}
            pdbFname= self._locateFname(pdbFname)
            if pdbFname is not None:
                algoDataDict= self._getJsonFromFname(pdbFname, chain_id, minToFilter= ANN_TYPES_MIN_VAL[algFamily][algoName] )
                if algoDataDict is not None:
                    algoDataDict["algorithm"]=algoName
                    algoDataDict["algoType"]=algFamily
                    responseData.append(algoDataDict)

        if len(responseData)==0:
          logger.debug("Not found %s", pdb_id+"/"+chain_id)
          return not_found_resp(pdb_id)

        return Response(responseData)


class DownloadModifiedPDB(APIView, PdbEntryLocResUtils):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, model_type, pdb_id, format=None):
        """
        Get fake data json for pdb_id, chain_id
        """
        pdb_id= pdb_id.lower()
        #TODO: implement this
        # entry= models.Entry.objects.get(entryId__iexact=pdb_id, entryType__iexact=ENTRY_TYPES[1])
        fileRecords= models.DataFile.objects.filter(entry__entryId=pdb_id, fileType__iexact=FILE_TYPES[1])
        logger.debug(fileRecords)

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
