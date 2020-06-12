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
        fields = ['entryId', 'path', 'files', 'entryType']

class DataSetNestedSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    class Meta:
        model = models.DataSet
        fields = ['features',]

class DataFileSerializer(serializers.ModelSerializer):
    data = DataFileNestedSerializer(many=True, read_only=True)
    class Meta:
        model = models.DataFile
        fields = ['unique_id', 'filename', 'entry', 'data', 'fileType']


class DataSetSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    class Meta:
        model = models.DataSet
        fields = ['file', 'features']


class UniprotEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UniprotEntry
        fields = '__all__'


class TrackTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TrackType
        fields = '__all__'


class FeatureDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TrackData
        fields = '__all__'

class FeatureDataDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TrackData
        fields = [
            'mutationType', 'mutationEffect',
            'begin', 'end',
            'wildtype', 'variation',
            'numberOfViruses',
            'reportedProtChange', 'genomicPosition', 'originalGenomic', 'newGenomic',
            'evidenceLevel']

class FeatureTrackSerializer(serializers.ModelSerializer):
    # acc <-> uniprot_entry = models.ForeignKey(UniprotEntry, related_name='tracks', on_delete=models.CASCADE)
    # visualization_type <-> track_type

    class Meta:
        model = models.FeatureTrack
        fields = '__all__'

class FeatureTrackDetailSerializer(serializers.ModelSerializer):
    track_name = serializers.SerializerMethodField('get_track_name')
    acc = serializers.SerializerMethodField('get_acc')
    visualization_type = serializers.SerializerMethodField('get_visualization_type')
    data = FeatureDataDetailSerializer(many=True)

    def get_track_name(self, obj):
        return obj.name

    def get_acc(self, obj):
        return obj.uniprot_entry.accession

    def get_visualization_type(self, obj):
        return obj.track_type.name

    class Meta:
        model = models.FeatureTrack
        fields = ['acc', 'visualization_type', 'track_name', 'reference', 'fav_icon', 'data']