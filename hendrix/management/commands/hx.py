import cPickle as pickle
import os
import time
import subprocess
from sys import executable
from path import path

from .options import HX_OPTION_LIST
from django.core.management.base import BaseCommand

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
        store_true = ['--nocache', '--global_cache', '--daemonize', '--dev']
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
    option_list = HX_OPTION_LIST

    def handle(self, *args, **options):
        action = args[0]
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
        elif options['daemonize']:
            daemonize = options.pop('daemonize')
            _options = []
            store_true = ['--nocache', '--global_cache', '--dev']
            store_false = []
            for key, value in options.iteritems():
                key = '--' + key
                if (key in store_true and value) or (key in store_false and not value):
                    _options += [key,]
                elif value:
                    _options += [key, str(value)]
            subprocess.Popen(['hx', action] + _options)
        else:
            deploy = HendrixDeploy(action, options)
            deploy.run()
