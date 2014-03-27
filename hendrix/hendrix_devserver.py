import os
import sys
import importlib

from . import import_wsgi
from .parser import HendrixParser
from .resources import get_additional_resources
from .services import HendrixService

from twisted.internet import reactor
from twisted.internet.error import CannotListenError


parser = HendrixParser().base_args()
args = vars(parser.parse_args())
settings = args.get('settings', 'settings.local')
os.environ['DJANGO_SETTINGS_MODULE'] = settings

PORT = args.get('port', 8000)
WSGI = args.get('wsgi', './wsgi.py')
wsgi_module = import_wsgi(WSGI)

from hendrix.contrib import DevWSGIHandler
settings_module = importlib.import_module(settings)

# If the user has wrapped the wsgi application in a Sentry instance then the
# django WSGIHandler instance will be hidden under the application attr.
wsgi = wsgi_module.application
wsgi.application = DevWSGIHandler()

server = HendrixService(
    wsgi, port=PORT,
    services=get_additional_services(settings_module),
    resources=get_additional_resources(settings_module)
)

try:
    server.startService()
    print ("Listening on port %s" % PORT)
    reactor.run()
except CannotListenError, e:
    thread_pool = server.services[0].pool
    thread_pool.stop()
    os.system( [ 'clear', 'cls' ][ os.name == 'nt' ] )
    exit(
        'Looks like you already have devserver running on this machine.'
        '\nPlease stop the other process before trying to launch a new one.'
    )
