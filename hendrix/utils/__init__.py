import os
import sys
import tempfile
from importlib import import_module

import chalk
import six

HENDRIX_DIR = os.path.dirname(os.path.abspath(__file__))

# Default PID Directory
PID_DIR = tempfile.mkdtemp(prefix='hendrix-')


SHARE_PATH = os.path.join(
    os.path.dirname(sys.executable),
    'share/hendrix'
)


def get_pid(options):
    """returns The default location of the pid file for process management"""
    namespace = options['settings'] if options['settings'] else options['wsgi']
    return os.path.join('{}', '{}_{}.pid').format(PID_DIR, options['http_port'], namespace.replace('.', '_'))


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
    signal = int(code) / 100
    if signal == 2:
        chalk.green(message, opts=opts)
    elif signal == 3:
        chalk.blue(message, opts=opts)
    else:
        chalk.red(message, opts=opts)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name
        )
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])
