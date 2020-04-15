from rest_framework import serializers
from localResWS.ws.models import Entry, EMResolutionMap


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = '__all__'
        

class ResoMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = EMResolutionMap
        exclude = ['local_path']