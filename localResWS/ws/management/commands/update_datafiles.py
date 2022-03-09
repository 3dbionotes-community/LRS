"""
Command for updating Ligand files
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import updateDB_modifiedPdbs



class Command(BaseCommand):
    """
    Command for updating Ligand files
    """

    help = "Update files <modelType>"
    missing_args_message = "Too few arguments. Please, provide a model type."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'modelType', nargs=1, type=str,
            help='<Required> Model type: isolde, pdb-redo, refmac')

    def handle(self, *args, **options):
        modelType = options['modelType'][0]
        print("Updating files for ", modelType)
        updateDB_modifiedPdbs(modelType)
