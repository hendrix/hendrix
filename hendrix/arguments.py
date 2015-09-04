import argparse
import os

from hendrix import defaults

usage = '''
hx -h
hx start|stop [--settings SETTINGS] [--log LOG]
              [--pythonpath PYTHONPATH] [--http_port HTTP_PORT]
              [--cache_port CACHE_PORT] [--dev]
hx start|stop [--http_port HTTP_PORT] [-d] [--dev] [--wsgi WSGI]
        
hx is the interface to hendrix, use to start and stop your server.

hx requires either --settings, --wsgi, or the DJANGO_SETTINGS_MODULE
environment variable be defined.
'''
HendrixParser = argparse.ArgumentParser(usage=usage)

def cleanOptions(options):
    """
    Takes an options dict and returns a tuple containing the daemonize boolean,
    the reload boolean, and the parsed list of cleaned options as would be
    expected to be passed to hx
    """
    daemonize = options.pop('daemonize')
    _reload = options.pop('reload')
    dev = options.pop('dev')
    opts = []
    store_true = [
        '--nocache', '--global_cache', '--traceback', '--quiet', '--loud'
    ]
    store_false = []
    for key, value in options.iteritems():
        key = '--' + key
        if (key in store_true and value) or (key in store_false and not value):
            opts += [key, ]
        elif value:
            opts += [key, str(value)]
    return daemonize, _reload, opts

HendrixParser.add_argument(
    'action',
    type=str,
    help='start|stop'
),
HendrixParser.add_argument(
    '-v', '--verbosity',
    action='store',
    dest='verbosity',
    default='1',
    type=int,
    choices=[0, 1, 2, 3],
    help=(
        'Verbosity level; 0=minimal output, 1=normal output, 2=verbose '
        'output, 3=very verbose output'
    )
),
HendrixParser.add_argument(
    '--settings',
    dest='settings',
    type=str,
    default='',
    help=(
        'The Python path to a settings module, e.g. "myproj.settings.x".'
        ' If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment '
        'variable will be used.'
    )
),
HendrixParser.add_argument(
    '--log',
    dest='log',
    type=str,
    default=os.path.join(defaults.DEFAULT_LOG_PATH, 'hendrix.log'),
    help=(
        'file path to where the log files should live '
        '[default: $PYTHON_PATH/lib/.../hendrix/hendrix.log]'
    )
),
HendrixParser.add_argument(
    '--pythonpath',
    help=(
        'A directory to add to the Python path, e.g. '
        '"/home/djangoprojects/myproject".'
    )
),
HendrixParser.add_argument(
    '--reload',
    action='store_true',
    dest='reload',
    default=False,
    help=(
        "Flag that watchdog should restart the server when changes to the "
        "codebase occur. NOTE: Do NOT uset this flag with --daemonize "
        "because it will not daemonize."
    )
),
HendrixParser.add_argument(
    '-l', '--loud',
    action='store_true',
    dest='loud',
    default=False,
    help="Use the custom verbose WSGI handler that prints in color"
),
HendrixParser.add_argument(
    '-q', '--quiet',
    action='store_true',
    dest='quiet',
    default=False,
    help="Supress all output."
),
HendrixParser.add_argument(
    '--http_port',
    type=int,
    dest='http_port',
    default=defaults.HTTP_PORT,
    help='Enter a port number for the server to serve content.'
),
HendrixParser.add_argument(
    '--https_port',
    type=int,
    dest='https_port',
    default=defaults.HTTPS_PORT,
    help='Enter an ssl port number for the server to serve secure content.'
),
HendrixParser.add_argument(
    '--cache_port',
    type=int,
    dest='cache_port',
    default=defaults.CACHE_PORT,
    help='Enter an cache port number to serve cached content.'
),
HendrixParser.add_argument(
    '-g', '--global_cache',
    dest='global_cache',
    action='store_true',
    default=False,
    help='Make it so that there is only one cache server'
),
HendrixParser.add_argument(
    '-c', '--cache',
    dest='cache',
    action='store_true',
    default=False,
    help='Disable page cache'
),
HendrixParser.add_argument(
    '-w', '--workers',
    type=int,
    dest='workers',
    default=0,
    help='Number of processes to run'
),
HendrixParser.add_argument(
    '--key',
    type=str,
    dest='key',
    default=None,
    help='Absolute path to SSL private key'
),
HendrixParser.add_argument(
    '--cert',
    type=str,
    dest='cert',
    default=None,
    help='Absolute path to SSL public certificate'
),
HendrixParser.add_argument(
    '--fd',
    type=str,
    dest='fd',
    default=None,
    help='DO NOT SET THIS'
),
HendrixParser.add_argument(
    '-d', '--daemonize',
    dest='daemonize',
    action='store_true',
    default=False,
    help='Run in the background'
),
HendrixParser.add_argument(
    '--dev',
    dest='dev',
    action='store_true',
    default=False,
    help=(
        'Runs in development mode. Meaning it uses the development wsgi '
        'handler subclass'
    )
),
HendrixParser.add_argument(
    '--wsgi',
    dest='wsgi',
    type=str,
    default=None,
    help='Overrides the use of django settings.'
)