"""
Command for removing duplicated DataFiles
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import removeDuplicateDataFiles



class Command(BaseCommand):
    """
    Command for removing duplicated DataFiles
    """

    help = "Remove DataFile by <filename>"
    missing_args_message = "Too few arguments. Please, valid DataFile filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'filetype', nargs=1, type=str,
            help='<Required> Remove from DB duplicated DataFiles with <filetype>.')

    def handle(self, *args, **options):
        filetype = options['filetype'][0]
        print("Removing duplicated DataFiles with: ", filetype)
        removeDuplicateDataFiles(filetype=filetype)
