import os
import subprocess
import sys
import time
import traceback
from path import path

from .options import HX_OPTION_LIST
from django.core.management.base import BaseCommand

from hendrix.deploy import HendrixDeploy

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def cleanOptions(options):
    """
    Takes an options dict and returns a tuple containing the daemonize boolean,
    the reload boolean, and the parsed list of cleaned options as would be
    expected to be passed to hx
    """
    daemonize = options.pop('daemonize')
    _reload = options.pop('reload')
    opts = []
    store_true = ['--nocache', '--global_cache', '--dev', '--traceback', '--quiet']
    store_false = []
    for key, value in options.iteritems():
        key = '--' + key
        if (key in store_true and value) or (key in store_false and not value):
            opts += [key,]
        elif value:
            opts += [key, str(value)]
    return daemonize, _reload, opts


class Reload(FileSystemEventHandler):

    def __init__(self, options, *args, **kwargs):
        super(Reload, self).__init__(*args, **kwargs)
        daemonize, self.reload, self.options = cleanOptions(options)
        if not self.reload:
            raise RuntimeError(
                'Reload should not be run if --reload has no been passed to '
                'the command as an option.'
            )
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
            if options['quiet']:
                raise RuntimeError('Do not use --daemonize and --quiet together')
            options['quiet'] = True
            daemonize, _reload, opts = cleanOptions(options)
            process = subprocess.Popen(['hx', action] + opts)
            time.sleep(2)
        else:
            try:
                deploy = HendrixDeploy(action, options)
                deploy.run()
            except Exception, e:
                if options.get('traceback'):
                    tb = sys.exc_info()[2]
                    msg = traceback.format_exc(tb)
                else:
                    msg = str(e)
                sys.stderr.write('\33[91m'+ msg + '\33[0m')
                os._exit(1)
