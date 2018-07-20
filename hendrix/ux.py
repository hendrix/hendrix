"""
A module to encapsulate the user experience logic
"""

from __future__ import with_statement

import os
import re
import subprocess
import sys
import time
import traceback

import chalk
from twisted.logger import globalLogPublisher
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from hendrix.contrib import SettingsError
from hendrix.deploy import base, cache
from hendrix.logger import hendrixObserver
from hendrix.mechanics.concurrency.exceptions import RedisException
from hendrix.options import cleanOptions
from .options import HendrixOptionParser

try:
    from tiempo.conn import REDIS
    from tiempo.locks import lock_factory

    redis_available = True
except ImportError:

    redis_available = False


class Reload(FileSystemEventHandler):

    def __init__(self, options, *args, **kwargs):
        super(Reload, self).__init__(*args, **kwargs)
        self.reload, self.options = cleanOptions(options)
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


def hendrixLauncher(action, options, with_tiempo=False):
    """
    Decides which version of HendrixDeploy to use and then
    launches it.
    """
    if options['key'] and options['cert'] and options['cache']:
        from hendrix.deploy import hybrid
        HendrixDeploy = hybrid.HendrixDeployHybrid
    elif options['key'] and options['cert']:
        from hendrix.deploy import tls
        HendrixDeploy = tls.HendrixDeployTLS
    elif options['cache']:
        HendrixDeploy = cache.HendrixDeployCache
    else:
        HendrixDeploy = base.HendrixDeploy
    if with_tiempo:
        deploy = HendrixDeploy(action='start', options=options)
        deploy.run()
    else:
        deploy = HendrixDeploy(action, options)
        deploy.run()


def assignDeploymentInstance(action, options):
    try:
        hendrixLauncher(action, options)
    except Exception as e:
        tb = sys.exc_info()[2]
        msg = traceback.format_exc(tb)
        chalk.red(msg, pipe=chalk.stderr)
        os._exit(1)


def logReload(options):
    """
    encompasses all the logic for reloading observer.
    """
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


def launch(*args, **options):
    """
    launch acts on the user specified action and options by executing
    Hedrix.run
    """
    action = args[0]
    if options['reload']:
        logReload(options)
    else:
        assignDeploymentInstance(action, options)


def findSettingsModule():
    "Find the settings module dot path within django's manage.py file"
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
                # os.environ.setdefault(
                #     "DJANGO_SETTINGS_MODULE", "example_app.settings"
                # )
                search = re.search(
                    "\".*?\"(,\\s)??\"(?P<module>.*?)\"\\)$",
                    manage_contents, re.I | re.S | re.M
                )
                settings_mod = search.group("module")

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_mod)
    except IOError as e:
        msg = (
                str(e) + '\nPlease ensure that you are in the same directory '
                         'as django\'s "manage.py" file.'
        )
        raise IOError(chalk.red(msg), None, sys.exc_info()[2])
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
            raise SettingsError(chalk.red(msg), None, sys.exc_info()[2])
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
        globalLogPublisher.addObserver(hendrixObserver(log_path))
    return None


def subprocessLaunch():
    """
    This function is called by the hxw script.
    It takes no arguments, and returns an instance of HendrixDeploy
    """
    if not redis_available:
        raise RedisException("can't launch this subprocess without tiempo/redis.")
    try:
        action = 'start'
        options = REDIS.get('worker_args')
        assignDeploymentInstance(action='start', options=options)
    except Exception:
        chalk.red('\n Encountered an unhandled exception while trying to %s hendrix.\n' % action, pipe=chalk.stderr)
        raise


def main(args=None):
    "The function to execute when running hx"
    if args is None:
        args = sys.argv[1:]
    options, args = HendrixOptionParser.parse_args(args)
    options = vars(options)

    try:
        action = args[0]
    except IndexError:
        HendrixOptionParser.print_help()
        return

    exposeProject(options)

    options = djangoVsWsgi(options)

    options = devFriendly(options)

    redirect = noiseControl(options)

    try:
        launch(*args, **options)
    except Exception:
        chalk.red('\n Encountered an unhandled exception while trying to %s hendrix.\n' % action, pipe=chalk.stderr)
        raise
