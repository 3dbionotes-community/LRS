import uuid

from django.db import models


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

class DataFile(models.Model):
    # entryId = models.ForeignKey(Entry, related_name='data_files', on_delete=models.CASCADE)
    # anntype = models.ForeignKey(AnnCategory, related_name='data_files', on_delete=models.CASCADE)

    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=50, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entry = models.ForeignKey(Entry, related_name='files', on_delete=models.CASCADE)
    # data_file = models.FileField(blank=True, default='')
