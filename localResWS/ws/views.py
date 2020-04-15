from django.shortcuts import render
from localResWS.ws.models import Volmap
from localResWS.ws.serializers import VolmapSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

class VolmapList(APIView):
    """
    List all volume maps
    """
    def get(self, request, format=None):
        volmaps = Volmap.objects.all()
        serializer = VolmapSerializer(volmaps, many=True)
        return Response(serializer.data)
