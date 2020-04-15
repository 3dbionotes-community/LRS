from django.db import models
import uuid

ANNOT_CATEGORIES = (('mr', 'MAP_RESOLUTION'),)
ANNOT_TYPES = (('lr', 'LOCAL_RESOLUTION'), ('bf', 'B_FACTOR'), ('mq', 'MAP_Q'))


class Entry(models.Model):
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50, blank=True, default='')
    description = models.CharField(max_length=255, blank=True, default='')
    local_path = models.CharField(max_length=255, blank=True, default='')
    volmaps = []
    pdbmodels = []

class Volmap(models.Model):

    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                 editable=False)
    title = models.CharField(max_length=50, blank=True, default='')
    ori_path = models.CharField(max_length=255, blank=True, default='')
    local_path = models.CharField(max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title + ", [" + str(self.unique_id) + "]" 

class EMResolutionMap(Volmap):

    # "category": "MAP_RESOLUTION"
    annotation_category = models.CharField(choices=ANNOT_CATEGORIES, blank=False, default='MAP_RESOLUTION', max_length=50)
    annotation_type = models.CharField(choices=ANNOT_TYPES, blank=False, default='LOCAL_RESOLUTION', max_length=50)
    map_gzfile = models.FileField(blank=True)
    