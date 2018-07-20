from django.core.management.base import BaseCommand

from hendrix.options import HX_OPTION_LIST
from hendrix.ux import launch


class Command(BaseCommand):
    option_list = HX_OPTION_LIST

    def handle(self, *args, **options):
        launch(*args, **options)
