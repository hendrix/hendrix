"""
A module to encapsulate the user experience logic
"""

import chalk
import os
import subprocess
import sys
import time
import traceback
from .options import HendrixOptionParser, cleanOptions
from hendrix.contrib import SettingsError
from hendrix.deploy import HendrixDeploy
from path import path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



class Reload(FileSystemEventHandler):

    def __init__(self, options, *args, **kwargs):
        super(Reload, self).__init__(*args, **kwargs)
        daemonize, self.reload, self.options = cleanOptions(options)
        if not self.reload:
            raise RuntimeError(
                'Reload should not be run if --reload has not been passed to '
                'the command as an option.'
            )
        self.process = subprocess.Popen(
            ['hx', 'start_reload'] + self.options
        )

    def on_any_event(self, event):
        if event.is_directory:
            return
        ext = path(event.src_path).ext
        if ext == '.py':
            self.process = self.restart()
            chalk.yellow("Detected changes, restarting...")

    def restart(self):
        self.process.terminate()
        process = subprocess.Popen(
            ['hx', 'restart'] + self.options
        )
        return process



def launch(*args, **options):
    "launch acts on the user specified action and options by executing Hedrix.run"
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
            chalk.red(msg, pipe=chalk.stderr)
            os._exit(1)


def djangoVsWsgi(options):
    # settings logic
    if not options['wsgi']:
        user_settings = options['settings']
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
        if not settings_module and not user_settings:
            msg = (
                'Either specify:\n--settings mysettings.dot.path\nOR\n'
                'export DJANGO_SETTINGS_MODULE="mysettings.dot.path"'
            )
            raise SettingsError(msg), None, sys.exc_info()[2]
        elif user_settings:
            options['settings'] = user_settings
        elif settings_module:
            options['settings'] = settings_module
    else:
        try:
            HendrixDeploy.importWSGI(options['wsgi'])
        except ImportError:
            raise ImportError("The path '%s' does not exist" % options['wsgi'])

    return options


def exposeProject(options):
    # sys.path logic
    if options['pythonpath']:
        project_path = path(options['pythonpath'])
        if not project_path.exists():
            raise IOError("The path '%s' does not exist" % project_path)
        sys.path.append(project_path)
    else:
        sys.path.append(os.getcwd())


def devFriendly(options):
    # if the dev option is given then also set reload to true
    # note that clean options will remove reload so to honor that we use get
    # in the second part of the conditional
    options['reload'] = True if options['dev'] else options.get('reload', False)
    options['loud'] = True if options['dev'] else options['loud']
    return options

def noiseControl(options):
    # terminal noise/info logic
    devnull = open(os.devnull, 'w')
    if options['quiet'] and not options['daemonize']:
        sys.stdout = devnull
        sys.stderr = devnull
    redirect = devnull if not options['traceback'] else None
    return redirect


def main():
    "The function to execute when running hx"
    options, args = HendrixOptionParser.parse_args(sys.argv[1:])
    options = vars(options)

    action = args[0]

    options = djangoVsWsgi(options)

    exposeProject(options)

    options = devFriendly(options)

    redirect = noiseControl(options)

    try:
        if action == 'start' and not options['daemonize']:
            chalk.blue('Starting Hendrix...')
        elif action == 'stop':
            chalk.green('Stopping Hendrix...')
        if options['daemonize']:
            daemonize, _reload, opts = cleanOptions(options)
            process = subprocess.Popen(['hx', action] + opts, stdout=redirect, stderr=redirect)
            time.sleep(2)
            if process.poll():
                raise RuntimeError
        else:
            launch(*args, **options)
            if not action == 'start_reload':
                chalk.green('\nHendrix successfully closed.')
    except Exception, e:
        msg = (
            'ERROR: %s\nCould not %s hendrix. Try again using the --traceback '
            'flag for more information.'
        )
        chalk.red(msg % (str(e), action), pipe=chalk.stderr)
        if options['traceback']:
            raise
        else:
            os._exit(1)
