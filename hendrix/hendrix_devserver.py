import os
import sys
import importlib
import argparse

from hendrix import import_wsgi
from hendrix.core import get_hendrix_resource

from twisted.internet import reactor
from twisted.internet.error import CannotListenError


parser = argparse.ArgumentParser(description="The Hendrix Development Server")
parser.add_argument('SETTINGS', help='Location of the settings object')
parser.add_argument('WSGI', help='Location of the wsgi object')
parser.add_argument('PORT', type=int, help='Enter a port number for the server to serve content.')
args = vars(parser.parse_args())
try:
    settings = args['SETTINGS']
except KeyError:
    settings = 'settings.local'
os.environ['DJANGO_SETTINGS_MODULE'] = settings

PORT = args['PORT']
WSGI = args['WSGI']
wsgi_module = import_wsgi(WSGI)

from hendrix.contrib import DevWSGIHandler
settings_module = importlib.import_module(settings)

# If the user has wrapped the wsgi application in a Sentry instance then the
# django WSGIHandler instance will be hidden under the application attr.
wsgi = wsgi_module.application
wsgi.application = DevWSGIHandler()



##########################################################################
# if HENDRIX_EXTRA_HANDLERS is specified in settings,
# it should be a list of tuples specifying a url path and a module path
# to a function which returns the handler that will process calls to that url
#
# example:
#
# HENDRIX_CHILD_HANDLERS = (
#   ('process', 'apps.offload.handlers.get_LongRunningProcessHandler'),
#   ('chat',    'apps.chat.handlers.get_ChatHandler'),
# )
#
# HENDRIX_CHILD_HANDLER_NAMESPACE = 'crosstowntraffic'#(optional)
#


additional_handlers = []

if hasattr(settings_module, 'HENDRIX_CHILD_HANDLERS'):
    namespace = getattr(settings_module,'HENDRIX_CHILD_NAMESPACE','hendrixchildren')

    for url_path, module_path in settings_module.HENDRIX_CHILD_HANDLERS:
        path_to_module, handler_generator = module_path.rsplit('.', 1)
        handler_module = importlib.import_module(path_to_module)

        #TODO:
        #
        #   ideally, we could namespace these handlers like this:
        #   /hendrixchildren/chat
        #   /hendrixchildren/chat
        #
        #   this should seemingly be done by creating nested proxy handlers which return handlers
        #   for their child paths.
        #

        additional_handlers.append(('%s-%s'%(namespace,url_path), getattr(handler_module, handler_generator)()))
    
resource, server = get_hendrix_resource(wsgi, settings_module, port=PORT, additional_handlers=additional_handlers)

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
