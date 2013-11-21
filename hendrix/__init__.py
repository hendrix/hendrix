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
