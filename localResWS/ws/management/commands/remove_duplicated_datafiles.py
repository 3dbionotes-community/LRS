"""
Command for removing duplicated DataFiles
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import removeDuplicateDataFiles



class Command(BaseCommand):
    """
    Command for removing duplicated DataFiles
    """

    help = "Remove duplicated DataFiles: same path + filename"
    requires_migrations_checks = True

    def handle(self, *args, **options):
        print("Removing duplicated DataFiles: same path + filename")
        removeDuplicateDataFiles()
