import uuid

from django.db import models

ENTRY_TYPES=["emdb", "pdbRemodel", "computationalModel", "modelAndLigand"]
FILE_TYPES=["PDB_ANN_FROM_MAP", "ISOLDE", "COMPUTATIONAL_MODEL", "PDB_LIGAND_POCKET"]

class AnnCategory(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()

    class Meta:
        ordering = ['created']

class AnnType(models.Model):
    category = models.ForeignKey(AnnCategory, related_name='types', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()

class Entry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    entryId = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entryType = models.CharField(max_length=12, blank=True, default='')

class DataFile(models.Model):
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=50, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entry = models.ForeignKey(Entry, related_name='files', on_delete=models.CASCADE)
    fileType = models.CharField(max_length=12, blank=True, default='')
    method = models.CharField(max_length=12, blank=True, default='')


class Feature(models.Model):
    start = models.IntegerField()
    end = models.IntegerField()
    f_type = models.IntegerField()
    f_category = models.IntegerField()
    description = models.CharField(max_length=255, blank=True, default='')

class DataSet(models.Model):
    file = models.ForeignKey(Entry, related_name='data', on_delete=models.CASCADE)
    features = Feature()


#  ######################################################################
class UniprotEntry(models.Model):
    """
    UniprotEntry
    """
    accession = models.CharField(max_length=30, blank=False, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    description = models.CharField(max_length=255, blank=True, null=True, default='')


class TrackType(models.Model):
    trackTypeId = models.CharField(max_length=30, blank=False, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    description = models.CharField(max_length=255, blank=True, null=True, default='')


class FeatureTrack(models.Model):
    # acc
    uniprot_entry = models.ForeignKey(UniprotEntry, related_name='tracks', on_delete=models.CASCADE)
    # visualization_type
    track_type = models.ForeignKey(TrackType, related_name='tracks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    reference = models.CharField(max_length=255, blank=True, null=True, default='')
    fav_icon = models.CharField(max_length=255, blank=True, null=True, default='')
    sequence = models.TextField(blank=True, null=True, default='')


class TrackData(models.Model):
    f_track = models.ForeignKey(FeatureTrack, related_name='features', on_delete=models.CASCADE)
    mutationType = models.CharField(max_length=255, blank=True, null=True, default='')
    sourceType = models.CharField(max_length=255, blank=True, null=True, default='')
    alternativeSequence = models.CharField(max_length=255, blank=True, null=True, default='')
    mutationEffect = models.CharField(max_length=255, blank=True, null=True, default='')
    begin = models.IntegerField()
    end = models.IntegerField()
    wildType = models.CharField(max_length=255, blank=True, null=True, default='')
    numberOfViruses = models.IntegerField()
    reportedProtChange = models.CharField(max_length=255, blank=True, null=True, default='')
    genomicPosition = models.IntegerField()
    originalGenomic = models.CharField(max_length=255, blank=True, null=True, default='')
    newGenomic = models.CharField(max_length=255, blank=True, null=True, default='')
    evidenceLevel = models.CharField(max_length=255, blank=True, null=True, default='')

class Xref(models.Model):
    feature = models.ForeignKey(TrackData, related_name='xrefs', on_delete=models.CASCADE)
    featureId = models.CharField(max_length=30, blank=True, null=True, default='')
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    url = models.CharField(max_length=255, blank=True, null=True, default='')
