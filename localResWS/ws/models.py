from django.db import models
import uuid


class Volmap(models.Model):

    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                                 editable=False)
    title = models.CharField(max_length=50, blank=True, default='')
    ori_path = models.CharField(max_length=255, blank=True, default='')
    local_path = models.CharField(max_length=255, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title + ", [" + str(self.unique_id) + "]" 

