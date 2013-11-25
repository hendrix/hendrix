try:
    from django.core.handlers.wsgi import WSGIHandler
except ImportError:
    raise ImportError(
        'Hendrix is a Django plugin. As such Django must be installed.'
    )


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