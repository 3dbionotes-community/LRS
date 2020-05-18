import os
import re

from subprocess import check_output

from django.core.exceptions import ValidationError

from localResWS.ws import models
from localResWS.ws.dataPaths import THORN_DATA_DIR, LOCAL_DATA_DIR, EMDB_BASEDIR, EMDB_DATA_DIR, MODIFIED_PDBS_ANN_DIR, \
  MODEL_AND_LIGAND_DIR
from localResWS.ws.models import ENTRY_TYPES, FILE_TYPES
import logging

logger = logging.getLogger(__name__)

PDB_FOLDER_PATTERN= re.compile(".*/(\d\w{3})/.*\.pdb$")

REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile('^(emd)-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile('^(pdb)\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAPQ_FILE = re.compile('^\d\w{3}\.(mapq)\.pdb$')


def findGeneric(pattern, dirToLook=THORN_DATA_DIR):
  data={}
  cmd=["find", os.path.join(dirToLook,"pdb"), "-wholename", pattern]
  logger.debug(" ".join(cmd))
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


def findIsolde(dirToLook=THORN_DATA_DIR):
  return findGeneric("*isolde/*pdb", dirToLook=dirToLook)

def findPdbRedo(dirToLook=THORN_DATA_DIR):
  return findGeneric("*/validation/pdb-redo/*final.pdb", dirToLook=dirToLook)


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
                                            entry=entry, fileType=FILE_TYPES[1], method=modelType)
                data_file.save()
            modifiedPdbsAnnDir= os.path.join(MODIFIED_PDBS_ANN_DIR, modelType, pdbId)
            # print(modifiedPdbsAnnDir)
            for fname in os.listdir(modifiedPdbsAnnDir):
              # print(fname)
              __, modelType, annType, __, __ = fname.split(".")
              data_file = models.DataFile(filename=fname, path=modifiedPdbsAnnDir,
                                          entry=entry, fileType=FILE_TYPES[0], method=annType)
              data_file.save()

            entry_list.append(entry)

    return entry_list


def updateDB_modelAndLigand(experimentName):
  entry_list = []
  if experimentName == "covid19_COSS":
    entryPath = os.path.join(MODEL_AND_LIGAND_DIR, experimentName)
    fnames = [ fname for fname in os.listdir(entryPath) if os.path.isdir(fname)]
  else:
    logger.debug('Error, experimentName %s not understood', experimentName)
    return []


  for pdbId in fnames:
    print("Updating %s ?"%pdbId)
    try:
      models.Entry.objects.get(entryId__iexact=pdbId, entryType__iexact=ENTRY_TYPES[3])
    except (models.Entry.DoesNotExist) as exc:
      logger.debug('Creating new ligand entry: %s', pdbId+"_"+ENTRY_TYPES[3])
      entry = models.Entry(entryId=pdbId, path=entryPath, entryType=ENTRY_TYPES[3])
      entry.save()
      # find files inside
      for filename in os.listdir(os.path.join(entryPath, pdbId)):
        if filename.endswith(".pdb"):
          logger.debug('Creating new dataFile %s record', filename)
          data_file = models.DataFile(filename=os.path.basename(filename), path=os.path.split(filename)[0],
                                      entry=entry, fileType=FILE_TYPES[1], method=experimentName)
          data_file.save()

      entry_list.append(entry)

  return entry_list




def getEntryAnnFromMapsFiles(entryId):
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

def updateDB_annoFromMaps(baseDir=EMDB_BASEDIR):
  logger.debug("Update DB from data folder: %s", LOCAL_DATA_DIR)
  reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAPQ_FILE]
  entry_list = []
  path = os.path.join(LOCAL_DATA_DIR, baseDir)
  try:
    dir_names = [f.name for f in os.scandir(path) if f.is_dir() and REGEX_EMDB_ID.match(f.name)]
    for dir_name in dir_names:
      # check if entry already exists
      try:
        models.Entry.objects.get(entryId__iexact=dir_name, entryType__iexact=ENTRY_TYPES[0])
      except (models.Entry.DoesNotExist) as exc:
        # logger.exception(exc)
        # new entry
        logger.debug('Creating new entry: %s from %s', dir_name, path)
        entry = models.Entry(entryId=dir_name, path=path, entryType=ENTRY_TYPES[0])
        entry.save()
        # find files inside
        logger.debug('Searching for datafiles: %s ', dir_name)
        dir_list = os.listdir(os.path.join(path, dir_name))
        for filename in dir_list:
          for reg_exp in reg_expressions:
            matchObj = reg_exp.match(filename)
            if matchObj:
              logger.debug('Found data file %s', filename)
              logger.debug('Creating new dataFile %s record', filename)
              data_file = models.DataFile(filename=filename, path=path, entry=entry, fileType=FILE_TYPES[0],
                                          method=matchObj.group(1))
              data_file.save()
        entry_list.append(entry)
  except() as exc:
    logger.exception(exc)

  return entry_list


class PdbEntryAnnFromMapsUtils(object):


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

    def _locateFname(self, targetFname, modifiedPdbType=None):

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

          if modifiedPdbType is None:
            rootDir= EMDB_DATA_DIR
          else:
            rootDir= os.path.join(MODIFIED_PDBS_ANN_DIR, modifiedPdbType)
          for dirName in os.listdir(rootDir):
            for fname in os.listdir(os.path.join(rootDir, dirName)):
                if fname== targetFname:
                    return os.path.join(rootDir, dirName, fname)
      return None