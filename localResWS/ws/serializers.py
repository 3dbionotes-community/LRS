from rest_framework import serializers
from localResWS.ws.models import Volmap


class VolmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volmap
        exclude = ['local_path']