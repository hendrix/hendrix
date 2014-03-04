import time
import subprocess
from path import path
from django.core.management.base import BaseCommand
from optparse import make_option

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Reload(FileSystemEventHandler):
    process = None
    port = None
    wsgi = None
    settings = None

    def __init__(self, wsgi, port, settings, *args, **kwargs):
        super(Reload, self).__init__(*args, **kwargs)
        self.port = port
        self.wsgi = wsgi
        self.settings = settings
        self.process = subprocess.Popen(
            ['hendrix-devserver.py', self.wsgi, self.port, self.settings]
        )

    def on_any_event(self, event):
        if event.is_directory:
            return
        ext = path(event.src_path).ext
        if ext in ['.py', '.html']:
            self.process = self.restart()
            print "Got it!"

    def restart(self):
        if self.process is not None:
            self.process.terminate()
        process = subprocess.Popen(
            ['hendrix-devserver.py', self.wsgi, self.port, self.settings]
        )
        return process


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--port',
            action='store',
            dest='port',
            default='8000',
            help='Set the web server port'),
        make_option(
            '--wsgi',
            action='store',
            dest='wsgi',
            default='./wsgi.py',
            help='Set the wsgi file path'),
        )

    def handle(self, *args, **options):
        port = options['port']
        wsgi = options['wsgi']
        settings = options['settings']
        event_handler = Reload(wsgi, port, settings)
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
