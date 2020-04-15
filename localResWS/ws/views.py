from django.shortcuts import render
from localResWS.ws.models import Entry
from localResWS.ws.serializers import EntrySerializer
from rest_framework.response import Response
from rest_framework.views import APIView
import logging
from django.conf import settings
from os import listdir
from os.path import join, isfile, isdir
import re

LOCAL_DATA_DIR = join(settings.BASE_DIR, 'service/data')

logger = logging.getLogger(__name__)


def readDataFolder():

    logger.info("Reading data folder %s", LOCAL_DATA_DIR)
    # get all dirs, every dir is an entry
    # dir_list = [d for d in listdir(LOCAL_DATA_DIR) if isdir(d)]
    dir_list = listdir(LOCAL_DATA_DIR)
    # get files in dir, every file is a different annotation type

    # add entries to DB
    for dir_name in dir_list:
        re_emdb_id = re.compile("^emd-\\d{4,5}$")
        if re_emdb_id.match(dir_name):
            try:
                entry = Entry.objects.get(title__iexact=dir_name)
                logger.info('Found dir entry $s', entry.title)
            except (Entry.DoesNotExist) as exc:
                # if new entry
                logger.info('Found new entry $s',dir_name)
                entry = Entry(title=dir_name, description='', local_path=join(LOCAL_DATA_DIR, dir_name))
                logger.info('Creating new entry: $s', entry.title)
            
            entry.save()


class EntryList(APIView):
    """
    List all entries
    """
    def get(self, request, format=None):
        # update list from disk
        readDataFolder()

        entries = Entry.objects.all()
        serializer = EntrySerializer(entries, many=True)
        return Response(serializer.data)
