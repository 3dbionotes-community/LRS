import os
import re

from subprocess import check_output


from localResWS.ws.dataPaths import THORN_BASEDIR
PDB_FOLDER_PATTERN= re.compile(".*/(\d\w{3})/.*\.pdb$")

def findIsolde(dirToLook=THORN_BASEDIR):
  data={}
  cmd=["find", os.path.join(dirToLook,"pdb"), "-wholename", "*isolde/*pdb"]
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


def findPdbRedo(dirToLook=THORN_BASEDIR):
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

