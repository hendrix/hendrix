import os, sys
import imp
# import autoreload

DEPLOYMENT_TYPE = "local"
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.local' #If the try block above did not cause exit, we know that this module exists.

from twisted.internet import reactor
from hendrix.deploy_functions import get_hendrix_resource
from hendrix.path_settings import * #Just to set the appropriate sys.path
from twisted.internet.error import CannotListenError

try:
    PORT = int(sys.argv[2])
    WSGI = imp.load_source('wsgi', sys.argv[1])
except IndexError:
    exit("usage: devserver.py <wsgi_module> <PORT>")

wsgi = WSGI.get_wsgi_handler('local')

resource, server = get_hendrix_resource(wsgi, 'settings.'+DEPLOYMENT_TYPE, port=PORT)

try:
    server.startService()
    print ("Listening on port %s" % PORT)
    reactor.run()
    # autoreload.main(reactor.run())
except CannotListenError, e:
    thread_pool = server.services[0].pool
    thread_pool.stop()
    os.system( [ 'clear', 'cls' ][ os.name == 'nt' ] )
    exit("Looks like you already have devserver running on this machine.\
    \nPlease stop the other process before trying to launch a new one.")