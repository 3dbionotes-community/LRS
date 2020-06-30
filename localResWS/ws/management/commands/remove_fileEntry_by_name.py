"""
Command for removing featureTracks by type
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import remove_fileEntry_by_name



class Command(BaseCommand):
    """
    Command for removing DataFile by filename
    """

    help = "Remove DataFile by <filename>"
    missing_args_message = "Too few arguments. Please, valid DataFile filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'filename', nargs=1, type=str,
            help='<Required> All DataFile with filename will be removed from DB.')

    def handle(self, *args, **options):
        filename = options['filename'][0]
        print("Removing DataFile with filename: ", filename)
        remove_fileEntry_by_name(filename=filename)
