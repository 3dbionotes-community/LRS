"""
Command for updating Ligand files
"""
from django.core.management.base import BaseCommand
from localResWS.ws.utils import updateLigandEntryFiles



class Command(BaseCommand):
    """
    Command for updating Ligand files
    """

    help = "Update  Ligand files <exp_name>"
    missing_args_message = "Too few arguments. Please, provide an experiment name."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'exp_name', nargs=1, type=str,
            help='<Required> Experiment name, i.e.: covid19_COSS')

    def handle(self, *args, **options):
        exp_name = options['exp_name'][0]
        print("Reading data for ", exp_name)
        updateLigandEntryFiles(exp_name=exp_name)
