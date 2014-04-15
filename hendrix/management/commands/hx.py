import time
import subprocess
from path import path
from django.core.management.base import BaseCommand
from optparse import make_option

from hendrix import defaults
from hendrix.deploy import HendrixDeploy

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Reload(FileSystemEventHandler):


    def __init__(self, options, *args, **kwargs):
        super(Reload, self).__init__(*args, **kwargs)
        self.reload = options.pop('reload')
        if not self.reload:
            raise RuntimeError(
                'Reload should not be run if --reload has no been passed to '
                'the command as an option.'
            )
        self.options = []
        store_true = ['--nocache', '--global_cache', '--daemonize']
        store_false = []
        for key, value in options.iteritems():
            key = '--' + key
            if (key in store_true and value) or (key in store_false and not value):
                self.options += [key,]
            elif value:
                self.options += [key, str(value)]
        self.process = subprocess.Popen(
            ['hx', 'start'] + self.options
        )

    def on_any_event(self, event):
        if event.is_directory:
            return
        ext = path(event.src_path).ext
        if ext == '.py':
            self.process = self.restart()
            print "Got it!"

    def restart(self):
        self.process.terminate()
        process = subprocess.Popen(
            ['hx', 'restart'] + self.options
        )
        return process


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--reload',
            action='store_true',
            dest='reload',
            default=False,
            help="Flag that watchdog should restart the server when changes to the codebase occur"
        ),
        make_option(
            '-l', '--loud',
            action='store_true',
            dest='loud',
            default=False,
            help="Show warnings"
        ),
        make_option(
            '--http_port',
            type=int,
            dest='http_port',
            default=defaults.HTTP_PORT,
            help='Enter a port number for the server to serve content.'
        ),
        make_option(
            '--https_port',
            type=int,
            dest='https_port',
            default=defaults.HTTPS_PORT,
            help='Enter an ssl port number for the server to serve secure content.'
        ),
        make_option(
            '--cache_port',
            type=int,
            dest='cache_port',
            default=defaults.CACHE_PORT,
            help='Enter an cache port number to serve cached content.'
        ),
        make_option(
            '-g', '--global_cache',
            dest='local_cache',
            action='store_true',
            default=False,
            help='Make it so that there is only one cache server'
        ),
        make_option(
            '-n', '--nocache',
            dest='nocache',
            action='store_true',
            default=False,
            help='Disable page cache'
        ),
        make_option(
            '-w', '--workers',
            type=int,
            dest='workers',
            default=0,
            help='Number of processes to run'
        ),
        make_option(
            '--key',
            type=str,
            dest='key',
            default=None,
            help='Absolute path to SSL private key'
        ),
        make_option(
            '--cert',
            type=str,
            dest='cert',
            default=None,
            help='Absolute path to SSL public certificate'
        ),
        make_option(
            '--fd',
            type=str,
            dest='fd',
            default=None,
            help='DO NOT SET THIS'
        ),
        make_option(
            '-d', '--daemonize',
            dest='daemonize',
            action='store_true',
            default=False,
            help='Run in the background'
        ),
    )

    def handle(self, *args, **options):
        if options['reload']:
            event_handler = Reload(options)
            observer = Observer()
            observer.schedule(event_handler, path='.', recursive=True)
            observer.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
            exit('\n')
        else:
            action = args[0]
            deploy = HendrixDeploy(action, options)
            deploy.run()
