import imp
import sys
from path import path
from django.core.handlers.wsgi import WSGIHandler


empty = object()
HENDRIX_DIR = path(__file__).abspath().dirname()
VIRTUALENV = path(sys.executable).parent.parent


def isempty(obj):
    return obj == empty


def exposeProject(_file):
    """
    When run in a module at the project level (i.e. above relevant python
    packages) subsequent packages, their contents and any modules at the same
    level will be exposed for use.
    """
    PROJECT_ROOT = path(_file).abspath().dirname()
    sys.path.append(PROJECT_ROOT)


class DevWSGIHandler(WSGIHandler):
    def __call__(self, *args, **kwargs):
        response = super(DevWSGIHandler, self).__call__(*args, **kwargs)
        print 'Response [%s] - %s:%s %s %s' % (
            response.status_code,
            args[0]['REMOTE_ADDR'],
            args[0]['SERVER_PORT'],
            args[0]['REQUEST_METHOD'],
            args[0]['PATH_INFO'],
        )
        return response


def import_wsgi(wsgi_path):
    _path = path(wsgi_path).abspath()
    if not _path.exists():
        raise RuntimeError('%s does not exist' % _path)
    wsgi_filename = _path.basename().splitext()[0]
    wsgi_dir = _path.parent
    try:
        _file, pathname, desc = imp.find_module(wsgi_filename, [wsgi_dir,])
        wsgi_module = imp.load_module(wsgi_filename, _file, pathname, desc)
        _file.close()
    except ImportError:
        raise RuntimeError('Could not import %s' % _path)
    return wsgi_module
