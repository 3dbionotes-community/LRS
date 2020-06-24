"""
Command for removing featureTracks by type
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import remove_tracks_by_type



class Command(BaseCommand):
    """
    Command for removing featureTracks by type
    """

    help = "Remove featureTracks by <type>"
    missing_args_message = "Too few arguments. Please, valid featureTrack type."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'track_type', nargs=1, type=str,
            help='<Required> All featureTracks of this type will be removed from DB.')

    def handle(self, *args, **options):
        track_type = options['track_type'][0]
        print("Removing featureTracks with type: ", track_type)
        remove_tracks_by_type(track_type=track_type)
