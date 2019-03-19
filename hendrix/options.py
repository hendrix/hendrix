import os
from optparse import make_option, OptionParser

from hendrix import defaults


def cleanOptions(options):
    """
    Takes an options dict and returns a tuple containing the daemonize boolean,
    the reload boolean, and the parsed list of cleaned options as would be
    expected to be passed to hx
    """
    _reload = options.pop('reload')
    dev = options.pop('dev')
    opts = []
    store_true = [
        '--nocache', '--global_cache', '--quiet', '--loud'
    ]
    store_false = []
    for key, value in options.items():
        key = '--' + key
        if (key in store_true and value) or (key in store_false and not value):
            opts += [key, ]
        elif value:
            opts += [key, str(value)]
    return _reload, opts


HX_OPTION_LIST = (
    make_option(
        '-v', '--verbosity',
        action='store',
        dest='verbosity',
        default='1',
        type='choice',
        choices=['0', '1', '2', '3'],
        help=(
            'Verbosity level; 0=minimal output, 1=normal output, 2=verbose '
            'output, 3=very verbose output'
        )
    ),
    make_option(
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
    make_option(
        '--log',
        dest='log',
        type=str,
        default=os.path.join(defaults.DEFAULT_LOG_PATH, 'hendrix.log'),
        help=(
            'file path to where the log files should live '
            '[default: $PYTHON_PATH/lib/.../hendrix/hendrix.log]'
        )
    ),
    make_option(
        '--pythonpath',
        help=(
            'A directory to add to the Python path, e.g. '
            '"/home/djangoprojects/myproject".'
        )
    ),
    make_option(
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
    make_option(
        '-l', '--loud',
        action='store_true',
        dest='loud',
        default=False,
        help="Use the custom verbose WSGI handler that prints in color"
    ),
    make_option(
        '-q', '--quiet',
        action='store_true',
        dest='quiet',
        default=False,
        help="Supress all output."
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
        '--https_only',
        dest='https_only',
        default=False,
        help='Declare whether to run only an https (not http) server.'
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
        dest='global_cache',
        action='store_true',
        default=False,
        help='Make it so that there is only one cache server'
    ),
    make_option(
        '-c', '--cache',
        dest='cache',
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
        '--dev',
        dest='dev',
        action='store_true',
        default=False,
        help=(
            'Runs in development mode. Meaning it uses the development wsgi '
            'handler subclass'
        )
    ),
    make_option(
        '--wsgi',
        dest='wsgi',
        type=str,
        default=None,
        help=(
            'Overrides the use of django settings for use in testing. N.B. '
            'This option is not for use with hx or hx.py'
        )
    )
)

HendrixOptionParser = OptionParser(
    description=(
        'hx is the interface to hendrix, use to start and stop your server'
    ),
    usage='hx start|stop [options]',
    option_list=HX_OPTION_LIST
)


def options(argv=[]):
    """
    A helper function that returns a dictionary of the default key-values pairs
    """
    parser = HendrixOptionParser
    parsed_args = parser.parse_args(argv)
    return vars(parsed_args[0])
