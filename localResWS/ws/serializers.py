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



class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Entry
        fields = ['id', 'entryId', 'path', 'created']

class DataFileSerializer(serializers.ModelSerializer):
    entryId = EntrySerializer()

    class Meta:
        model = models.Entry
        fields = '__all__'