import os, sys
DEPLOYMENT_TYPE = "local"
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.local' #If the try block above did not cause exit, we know that this module exists.

from twisted.internet import reactor
from deploy_functions import get_hendrix_resource
from path_settings import * #Just to set the appropriate sys.path
from twisted.internet.error import CannotListenError

try:
    PORT = int(sys.argv[1])
except IndexError:
    print("usage: devserver.py <PORT>")

resource, application, server = get_hendrix_resource(DEPLOYMENT_TYPE, port=PORT)

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