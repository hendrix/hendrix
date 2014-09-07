import chalk
import os
import sys


HENDRIX_DIR = os.path.dirname(os.path.abspath(__file__))

SHARE_PATH = os.path.join(
    os.path.dirname(sys.executable),
    'share/hendrix'
)


def get_pid(options):
    """returns The default location of the pid file for process management"""
    namespace = options['settings'] if options['settings'] else options['wsgi']
    return '%s/%s_%s.pid' % (
        HENDRIX_DIR, options['http_port'], namespace.replace('.', '_')
    )


def responseInColor(request, status, headers, prefix='Response', opts=None):
    "Prints the response info in color"
    code, message = status.split(None, 1)
    message = '%s [%s] => Request %s %s %s on pid %d' % (
        prefix,
        code,
        str(request.host),
        request.method,
        request.path,
        os.getpid()
    )
    signal = int(code)/100
    if signal == 2:
        chalk.green(message, opts=opts)
    elif signal == 3:
        chalk.blue(message, opts=opts)
    else:
        chalk.red(message, opts=opts)
