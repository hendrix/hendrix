import os
import sys
import imp
import importlib

from path import path

from hendrix import DevWSGIHandler
from hendrix.core import get_hendrix_resource

from twisted.internet import reactor
from twisted.internet.error import CannotListenError


try:
    PORT = int(sys.argv[2])
    WSGI = sys.argv[1]
    wsgi_path = path(WSGI).abspath()
    if not wsgi_path.exists():
        raise RuntimeError('%s does not exist' % wsgi_path)
    wsgi_filename = wsgi_path.basename().splitext()[0]
    wsgi_dir = wsgi_path.parent
    try:
        _file, pathname, desc = imp.find_module(wsgi_filename, [wsgi_dir,])
        wsgi_module = imp.load_module(wsgi_filename, _file, pathname, desc)
        _file.close()
    except ImportError:
        raise RuntimeError('Could not import %s' % wsgi_path)
except IndexError:
    exit("Usage: hendrix-devserver.py <WSGI> <PORT> [<SETTINGS>]")

# If the user has wrapped the wsgi application in a Sentry instance then the
# django WSGIHandler instance will be hidden under the application attr.
wsgi = wsgi_module.application
wsgi.application = DevWSGIHandler()

try:
    settings = sys.argv[3]
except KeyError:
    settings = 'settings.local'
os.environ['DJANGO_SETTINGS_MODULE'] = settings
settings_module = importlib.import_module(settings)

resource, server = get_hendrix_resource(wsgi, settings_module, port=PORT)

try:
    server.startService()
    print ("Listening on port %s" % PORT)
    reactor.run()
except CannotListenError, e:
    thread_pool = server.services[0].pool
    thread_pool.stop()
    os.system( [ 'clear', 'cls' ][ os.name == 'nt' ] )
    exit("Looks like you already have devserver running on this machine.\
    \nPlease stop the other process before trying to launch a new one.")