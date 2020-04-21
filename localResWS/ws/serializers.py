from rest_framework import serializers
from localResWS.ws import models


class TypeNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AnnType
        fields = ['id', 'title', 'description']

class CategorySerializer(serializers.HyperlinkedModelSerializer):
    types = TypeNestedSerializer(many=True)

    class Meta:
        model = models.AnnCategory
        fields = ['id', 'title', 'description', 'created' ,'types']

class CategoryNestedSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.AnnCategory
        fields = ['id', 'title']


class TypeSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer()

    class Meta:
        model = models.AnnType
        fields = ['id', 'title', 'description', 'created', 'category']


class DataFileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DataFile
        fields = ['filename', 'unique_id']

class EntrySerializer(serializers.ModelSerializer):
    files = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = models.Entry
        fields = ['entryId', 'path', 'files']

class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DataFile
        fields = ['unique_id', 'filename', 'entry', 'path']
