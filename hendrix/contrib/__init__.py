import sys
try:
    from django.core.handlers.wsgi import WSGIHandler
except ImportError as e:
    raise ImportError(
        str(e) + '\n' +
        'Hendrix is a Django plugin. As such Django must be installed.'
    ), None, sys.exc_info()[2]


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
