"""
Command for updating Features
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import read_feature_tracks



class Command(BaseCommand):
    """
    Command for updating Features
    """

    help = "Update Features from <path>/<ACC>_annotations.json"
    missing_args_message = "Too few arguments. Please, provide a folder name for the data JSON files."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'path', nargs=1, type=str,
            help='<Required> path to a directory containing JSON data files')
        parser.add_argument(
            'track_name', nargs=1, type=str,
            help='<Required> Track name as described in the JSON file, i.e.: Genomic_Variants_CNCB')

    def handle(self, *args, **options):
        path = options['path'][0].strip("/")
        track_name = options['track_name'][0]
        print("Reading data from ", path, " ", track_name)
        read_feature_tracks(path=path, track_name=track_name)
