from hendrix.ux import launch
from hendrix.options import HX_OPTION_LIST
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    option_list = HX_OPTION_LIST

    def handle(self, *args, **options):
        launch(*args, **options)
