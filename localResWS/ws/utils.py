import os
import re

from subprocess import check_output

from localResWS.ws import models
from localResWS.ws.dataPaths import THORN_DATA_DIR
from localResWS.ws.models import ENTRY_TYPES, FILE_TYPES
from localResWS.ws.views import logger

PDB_FOLDER_PATTERN= re.compile(".*/(\d\w{3})/.*\.pdb$")

def findIsolde(dirToLook=THORN_DATA_DIR):
  data={}
  cmd=["find", os.path.join(dirToLook,"pdb"), "-wholename", "*isolde/*pdb"]
  print(" ".join(cmd))
  isoldesCandidates= check_output(cmd ).decode()
  for candidate in isoldesCandidates.split("\n"):
    matchObj= re.match(PDB_FOLDER_PATTERN, candidate)
    if matchObj:
      pdbId= matchObj.group(1)
      try:
        data[pdbId].append(candidate)
      except KeyError:
        data[pdbId]=[candidate]
  return data


def findPdbRedo(dirToLook=THORN_DATA_DIR):
  data={}
  cmd=["find", os.path.join(dirToLook,"pdb"), "-wholename", "*pdb-redo/*final.pdb"]
  pdbRedoCandidates= check_output(cmd ).decode()
  for candidate in pdbRedoCandidates.split("\n"):
    if "isolde" in candidate: continue
    matchObj= re.match(PDB_FOLDER_PATTERN, candidate)
    if matchObj:
      pdbId= matchObj.group(1)
      try:
        data[pdbId].append(candidate)
      except KeyError:
        data[pdbId]=[candidate]
  return data

def updateDB_modifiedPdbs(modelType):
    entry_list=[]
    if modelType=="isolde":
        dataFunc= findIsolde
    elif modelType=="pdb-redo":
        dataFunc= findPdbRedo
    else:
        logger.debug('Error, modelType %s not understood', modelType)
        return []

    for pdbId, listOfFnames in dataFunc().items():
        try:
            models.Entry.objects.get(entryId__iexact=pdbId, entryType__iexact=ENTRY_TYPES[1])
        except (models.Entry.DoesNotExist) as exc:
            logger.debug('Creating new isolde entry: %s', pdbId)
            entry = models.Entry(entryId=pdbId, path=THORN_DATA_DIR, entryType=ENTRY_TYPES[1])
            entry.save()
            # find files inside
            for filename in listOfFnames:
                logger.debug('Creating new dataFile %s record', filename)
                data_file = models.DataFile(filename=os.path.basename(filename), path=os.path.split(filename)[0],
                                            entry=entry, fileType=FILE_TYPES[1])
                data_file.save()
            entry_list.append(entry)

    return entry_list








def dataFnameToDownloadUrl(dtype, pdbId, uuid):
  uuid= str(uuid)
  newUrl="files/modifiedPdb/download/%(modelType)s/%(pdbId)s/%(uuid)s"%locals()

