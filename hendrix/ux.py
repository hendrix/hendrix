"""
A module to encapsulate the user experience logic
"""

from __future__ import with_statement

import chalk
import os
import re
import subprocess
import sys
import time
import traceback
from .options import HendrixOptionParser, cleanOptions
from hendrix.contrib import SettingsError
from hendrix.deploy import base, ssl, cache, hybrid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from twisted.python import log
from twisted.python.logfile import DailyLogFile


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
        ext = os.path.splitext(event.src_path)[1]
        if ext == '.py':
            self.process = self.restart()
            chalk.eraser()
            chalk.yellow("Detected changes, restarting...")

    def restart(self):
        self.process.kill()
        process = subprocess.Popen(
            ['hx', 'start_reload'] + self.options
        )
        return process


def launch(*args, **options):
    """
    launch acts on the user specified action and options by executing
    Hedrix.run
    """
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
            pid = os.getpid()
            chalk.eraser()
            chalk.green('\nHendrix successfully closed.')
            os.kill(pid, 15)
        observer.join()
        exit('\n')
    else:
        try:
            if options['key'] and options['cert'] and options['cache']:
                HendrixDeploy = hybrid.HendrixDeployHybrid
            elif options['key'] and options['cert']:
                HendrixDeploy = ssl.HendrixDeploySSL
            elif options['cache']:
                HendrixDeploy = cache.HendrixDeployCache
            else:
                HendrixDeploy = base.HendrixDeploy
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


def findSettingsModule():
    "Find the settings module dot path within django's mnanage.py file"
    try:
        with open('manage.py', 'r') as manage:
            manage_contents = manage.read()

            search = re.search(
                r"([\"\'](?P<module>[a-z\.]+)[\"\'])", manage_contents
            )
            if search:  # django version < 1.7
                settings_mod = search.group("module")

            else:
# in 1.7, manage.py settings declaration looks like:
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_app.settings")
                search = re.search(
                    "\".*?\"(,\\s)??\"(?P<module>.*?)\"\\)$",
                    manage_contents, re.I | re.S | re.M
                )
                settings_mod = search.group("module")

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_mod)
    except IOError, e:
        msg = (
            str(e) + '\nPlease ensure that you are in the same directory '
            'as django\'s "manage.py" file.'
        )
        raise IOError(chalk.format_red(msg)), None, sys.exc_info()[2]
    except AttributeError:
        settings_mod = ''
    return settings_mod


def djangoVsWsgi(options):
    # settings logic
    if not options['wsgi']:
        settings_mod = findSettingsModule()
        user_settings = options['settings']
        if not settings_mod and not user_settings:
            msg = (
                '\nEither specify:\n--settings mysettings.dot.path\nOR\n'
                'export DJANGO_SETTINGS_MODULE="mysettings.dot.path"\nOR\n'
                'in your manage.py file specify '
                'os.environ.setdefault("DJANGO_SETTINGS_MODULE", '
                '"mysettings.dot.path")'
            )
            raise SettingsError(chalk.format_red(msg)), None, sys.exc_info()[2]
        elif user_settings:
            # if the user specified the settings to use then these take
            # precedence
            options['settings'] = user_settings
        elif settings_mod:
            options['settings'] = settings_mod
    else:
        try:
            base.HendrixDeploy.importWSGI(options['wsgi'])
        except ImportError:
            raise ImportError("The path '%s' does not exist" % options['wsgi'])

    return options


def exposeProject(options):
    # sys.path logic
    if options['pythonpath']:
        project_path = options['pythonpath']
        if not os.path.exists(project_path):
            raise IOError("The path '%s' does not exist" % project_path)
        sys.path.append(project_path)
    else:
        sys.path.append(os.getcwd())


def devFriendly(options):
    # if the dev option is given then also set reload to true
    # note that clean options will remove reload so to honor that we use get
    # in the second part of the conditional
    dev_mode = options['dev']
    options['reload'] = True if dev_mode else options.get('reload', False)
    options['loud'] = True if dev_mode else options['loud']
    return options


def noiseControl(options):
    # terminal noise/info logic
    # allows the specification of the log file location
    if not options['loud']:
        log_path = options['log']
        log.startLogging(DailyLogFile.fromFullPath(log_path))
    return None


def main():
    "The function to execute when running hx"
    options, args = HendrixOptionParser.parse_args(sys.argv[1:])
    options = vars(options)

    action = args[0]

    exposeProject(options)

    options = djangoVsWsgi(options)

    options = devFriendly(options)

    redirect = noiseControl(options)

    try:
        if action == 'start' and not options['daemonize']:
            chalk.eraser()
            chalk.blue('Starting Hendrix...')
        elif action == 'stop':
            chalk.green('Stopping Hendrix...')
        if options['daemonize']:
            daemonize, _reload, opts = cleanOptions(options)
            process = subprocess.Popen(
                ['hx', action] + opts, stdout=redirect, stderr=redirect
            )
            time.sleep(2)
            if process.poll():
                raise RuntimeError
        else:
            launch(*args, **options)
            if action not in ['start_reload', 'restart']:
                chalk.eraser()
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
