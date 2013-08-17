import os, sys
from path import path

from django.core.handlers.wsgi import WSGIHandler
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

where_are_we = path(__file__).abspath().dirname()

print "you are here: %s" % where_are_we

sys.path.append(where_are_we)

class HendrixWSGIHandler(WSGIHandler):

    def __init__(self, settings, *args, **kwargs):
        self.settings = settings
        return super(HendrixWSGIHandler, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        response = super(HendrixWSGIHandler, self).__call__(*args, **kwargs)
        if self.settings == "local":
            print '%s - %s %s %s' % (
                response.status_code,
                args[0]['REMOTE_ADDR'],
                args[0]['REQUEST_METHOD'],
                args[0]['PATH_INFO'],
            )
        return response

def get_wsgi_handler(settings):
    return Sentry(HendrixWSGIHandler(settings=settings))