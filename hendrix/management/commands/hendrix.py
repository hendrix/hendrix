import subprocess
from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--port',
            action='store_const',
            dest='port',
            default='8000',
            help='Set the web server port'),
        make_option(
            '--wsgi',
            action='store_const',
            dest='wsgi',
            default='./wsgi.py',
            help='Set the wsgi file path'),
        )

    def handle(self, *args, **options):
        port = options['port']
        wsgi = options['wsgi']
        settings = options['settings']
        try:
            subprocess.check_call(
                ['hendrix-devserver.py', wsgi, port, settings]
            )
        except KeyboardInterrupt:
            exit('\n')
