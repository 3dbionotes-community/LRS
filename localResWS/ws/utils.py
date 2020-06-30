import json
import logging
import os
import re
from subprocess import check_output

from django.core.exceptions import ValidationError

from localResWS.ws import models
from localResWS.ws.dataPaths import (EMDB_BASEDIR, EMDB_DATA_DIR,
                                     LOCAL_DATA_DIR, MODEL_AND_LIGAND_DIR,
                                     MODIFIED_PDBS_ANN_DIR, THORN_DATA_DIR)
from localResWS.ws.models import ENTRY_TYPES, FILE_TYPES

logger = logging.getLogger(__name__)

PDB_FOLDER_PATTERN= re.compile(".*/(\d\w{3})/.*\.pdb$")

REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile('^(emd)-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile('^(pdb)\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAP2MODELQUALITY_FILE = re.compile('^\d\w{3}\.(mapq|fscq)\.pdb$')


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
            if os.path.isdir(modifiedPdbsAnnDir):
              for fname in os.listdir(modifiedPdbsAnnDir):
                print(fname)
                __, modelType_, annType, __, __ = fname.split(".")
                data_file = models.DataFile(filename=fname, path=modifiedPdbsAnnDir,
                                            entry=entry, fileType=FILE_TYPES[0], method=annType)
                data_file.save()

            entry_list.append(entry)

    return entry_list


def updateDB_modelAndLigand(experimentName):
  print("updateDB_modelAndLigand")
  entry_list = []
  if experimentName == "covid19_COSS":
    entryPath = os.path.join(MODEL_AND_LIGAND_DIR, experimentName)
    fnames = [ fname for fname in os.listdir(entryPath) if os.path.isdir(os.path.join(entryPath,fname))]
  else:
    logger.debug('Error, experimentName %s not understood', experimentName)
    return []

  for pdbId in fnames:
    print("Updating ligands for %s ?"%pdbId)
    try:
      models.Entry.objects.get(entryId__iexact=pdbId, entryType__iexact=ENTRY_TYPES[3])
    except (models.Entry.DoesNotExist) as exc:
      logger.debug('Creating new ligand entry: %s', pdbId+"_"+ENTRY_TYPES[3])
      entry = models.Entry(entryId=pdbId, path=entryPath, entryType=ENTRY_TYPES[3])
      entry.save()
      # find files inside
      dirName= os.path.join(entryPath, pdbId)
      for filename in os.listdir(dirName):
        if filename.endswith(".pdb"):
          logger.debug('Creating new dataFile %s record', filename)
          data_file = models.DataFile(filename=os.path.basename(filename), path=dirName,
                                      entry=entry, fileType=FILE_TYPES[3], method=experimentName)
          data_file.save()

      entry_list.append(entry)

  return entry_list


def updateLigandEntryFiles(exp_name):
  print("updateLigandEntryFiles")
  if exp_name == "covid19_COSS":
    entryPath = os.path.join(MODEL_AND_LIGAND_DIR, exp_name)
    fnames = [ fname for fname in os.listdir(entryPath) if os.path.isdir(os.path.join(entryPath,fname))]
  else:
    logger.debug('Error, experimentName %s not understood', exp_name)
    return []
  
  for pdbId in fnames:
    print("Updating ligands for %s ?"%pdbId)
    try:
      # update or create PdbToUniprotMap
      entry, created = models.Entry.objects.update_or_create(
        entryId=pdbId,
        path=entryPath,
        entryType="modelAndLigand",)
      if created:
        logger.debug('Created new entry: %s', entry)
        print('Created new entry: ', entry)

      # find files inside
      dirName= os.path.join(entryPath, pdbId)
      for filename in os.listdir(dirName):
        if filename.endswith(".pdb"):
          logger.debug('Creating new dataFile %s record', filename)      
          # update or create PdbToUniprotMap
          data_file, created = models.DataFile.objects.update_or_create(
            entry=entry,
            filename= filename,
            path=entryPath,
            defaults={
              'method':"",
              'fileType':FILE_TYPES[3]})
          if created:
            logger.debug('Created new data_file: %s', filename)
            print('Created new data_file: ', filename)
    except()  as exc:
      logger.debug(exc)


def getEntryAnnFromMapsFiles(entryId):
    logger.debug("Get entry files for %s", entryId)
    path = os.path.join(LOCAL_DATA_DIR, entryId)
    reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAP2MODELQUALITY_FILE]
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
  reg_expressions = [REGEX_VOL_FILE, REGEX_PDB_FILE, REGEX_LR_FILE, REGEX_MAP2MODELQUALITY_FILE]
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


#  ######################################################################
def _update_uniprot_entry(accession, name=None, description=None):
    try:
        # update or create UniprotEntry
        obj, created = models.UniprotEntry.objects.update_or_create(
            accession=accession,
            defaults={
                'name': name if name else '',
                'description': description if description else '',})
        if created:
            logger.debug('Created new entry: %s', obj)
    except() as exc:
        logger.exception(exc)
    return obj

def _update_track_type(trackTypeId, name=None, description=None):
    try:
        # update or create TrackType
        obj, created = models.TrackType.objects.update_or_create(
            trackTypeId=trackTypeId,
            defaults={
                'name': name if name else trackTypeId.title(),
                'description': description if description else '',})
        if created:
            logger.debug('Created new entry: %s', obj)
    except() as exc:
        logger.exception(exc)
    return obj

def read_feature_tracks(path, track_name = None):
    """
    Read FeatureTracks
    """
    logger.debug("Updating Features from : %s", path)
    # data must be in <path>/<ACC>_annotations.json files
    objs = []
    try:
        data_files = [x for x in os.listdir(path) if x.endswith("_annotations.json")]
        for file_name in data_files:
            logger.debug('Reading JSON data from %s', file_name)
            with open(os.path.join(path, file_name)) as json_file:
                data = json.load(json_file)
                for track in data:
                    t_name = track['track_name']
                    if t_name == track_name:
                        accession = track["acc"]
                        # check sequence is not empty
                        if track["sequence"] == "":
                          raise ValueError('Sequence field can´t be empty.', accession, track["sequence"]) 
                        uniprot_entry = _update_uniprot_entry(accession=accession)

                        visualization_type = track["visualization_type"] if "visualization_type" in track else 'basic'
                        if visualization_type.upper() == "VARIANTS":
                          raise ValueError('Wrong visualization_type value. Must be VARIANT, not VARIANTS', visualization_type) 
                        track_type = _update_track_type(trackTypeId=visualization_type)

                        feature_track = _update_feature_track(uniprot_entry, track_type, track)
                        objs.append(feature_track)
    except() as exc:
        logger.exception(exc)
    return objs

def _update_feature_track(uniprot_entry, track_type, track):
    """
    Update FeatureTrack
    """
    objs = []
    track_name = track['track_name']
    logger.debug('Updating Feature: %s %s %s', uniprot_entry, track_type, track_name)
    print(uniprot_entry, track_type, track_name)
    try:
        # update or create FeatureTrack        
        feat_track, created = models.FeatureTrack.objects.update_or_create(
            uniprot_entry=uniprot_entry,
            name=track_name,
            track_type=track_type,
            defaults={
                'sequence': track["sequence"] if "sequence" in track else '',
                'reference': track["reference"] if "reference" in track else '',
                'fav_icon': track["fav_icon"] if "fav_icon" in track else ''})
        if created:
            logger.debug('Created new entry: %s', feat_track)
            objs.append(feat_track)

        for elem in track['data']:
            # update or create TrackData
            track_data, created = models.TrackData.objects.update_or_create(
                f_track=feat_track,
                begin=elem["begin"] if "begin" in elem else 0,
                end=elem["end"] if "end" in elem else 0,
                mutationType=elem["mutationType"] if "mutationType" in elem else '',
                mutationEffect=elem["mutationEffect"] if "mutationEffect" in elem else '',
                defaults={
                    'sourceType': elem["sourceType"] if "sourceType" in elem else 'large_scale_study',
                    'alternativeSequence': elem["variation"] if "variation" in elem else '',
                    'wildType': elem["wildtype"] if "wildtype" in elem else '',
                    'numberOfViruses': elem["numberOfViruses"] if "numberOfViruses" in elem else 0,
                    'reportedProtChange': elem["reportedProtChange"] if "reportedProtChange" in elem else '',
                    'genomicPosition': elem["genomicPosition"] if "genomicPosition" in elem else 0,
                    'originalGenomic': elem["originalGenomic"] if "originalGenomic" in elem else '',
                    'newGenomic': elem["newGenomic"] if "newGenomic" in elem else '',
                    'evidenceLevel': elem["evidenceLevel"] if "evidenceLevel" in elem else ''})
            if created:
                logger.debug('Created new entry: %s', track_data)
            
            for elem in elem["xrefs"]:
              # update or create Xref
              xref, created = models.Xref.objects.update_or_create(
                feature=track_data,
                featureId=elem["id"],
                name=elem["name"] if "name" in elem else '',
                defaults={
                    'url': elem["url"] if "url" in elem else '',})
            if created:
                logger.debug('Created new entry: %s', track_data)


    except() as exc:
        logger.exception(exc)
    return objs

def remove_tracks_by_type(track_type):
    """
      Remove FeatureTracks by type
    """
    logger.debug("Removing FeatureTracks by: %s", track_type)
    print("Removing FeatureTracks by: ", track_type)
    objs = []
    try:
        tracks = models.FeatureTrack.objects.filter(track_type=track_type)
        for track in tracks:
            logger.debug("Deleting : %s", track.id)
            print("Deleting : ", track.id)
            track.delete()
    except() as exc:
        logger.exception(exc)
    return objs


def remove_fileEntry_by_name(filename):
    """
      Remove DataFile by filename
    """
    logger.debug("Removing DataFile by : %s", filename)
    print("Removing DataFile by: ", filename)
    objs = []
    try:
        entry_files = models.DataFile.objects.filter(filename__contains=filename)
        for entry_file in entry_files:
            logger.debug("Deleting : %s", entry_file.filename)
            print("Deleting : ", entry_file.filename)
            entry_file.delete()
    except() as exc:
        logger.exception(exc)
    return objs


def removeDuplicateDataFiles():
  """
  Remove duplicated DataFiles
  """
  logger.debug("Searching for duplicated DataFiles: same path + filename")
  print("Searching for duplicated DataFiles: same path + filename")
  objs = []
  try:
      for row in models.DataFile.objects.all().reverse():
        if models.DataFile.objects.filter(path=row.path, filename=row.filename).count() > 1:
            logger.debug("Deleting : %s", row.filename)
            print("Deleting : ", row.filename, row.unique_id)
            # row.delete()
  except() as exc:
      logger.exception(exc)
  return objs

