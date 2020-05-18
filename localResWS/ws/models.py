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
