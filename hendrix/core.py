import sys
from twisted.application import internet, service
from twisted.internet import reactor, protocol
from twisted.python.threadpool import ThreadPool
from twisted.web import server, resource, static
from twisted.web.wsgi import WSGIResource
from twisted.web import resource

from .contrib import NamedResource

import logging

logger = logging.getLogger(__name__)


class HendrixService(service.MultiService):

    def __init__(self, application, port=80, resources=None, services=None, host=None):
        service.MultiService.__init__()

        # Create, start and add a thread pool service, which is made available
        # to our WSGIResource within HendrixResource
        threads = ThreadPool()
        reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)
        ThreadPoolService(threads).setServiceParent(self)

        # create the base resource and add any additional static resources
        self.resource = HendrixResource(reactor, threads, application)
        if resources:
            for res in resources:
                self.resource.putNamedChild(res)


        # create the base server/client
        factory = server.Site(self.resource)
        if host:
            factory = protocol.ReconnectingClientFactory(factory)
            internet.connectTCP(host, port, factory).setServiceParent(self)
        else:
            # add a tcp server that binds to port=port
            internet.listenTCP(port, factory).setServiceParent(self)

        # add any additional services
        if services:
            for srv in services:
                srv.setServiceParent(self)


def get_hendrix_resource(application, settings_module=None, port=80, additional_resources=None):
    '''
    Pseudo factory that returns the proper Resource object.
    Takes a deployment type and (for development) a port number.
    Returns a tuple (Twisted Resource, Twisted Service)
    '''
    # Create and start a thread pool,
    threads = ThreadPool()

    # The pool will stop when the reactor shuts down
    reactor.addSystemEventTrigger('after', 'shutdown', threads.stop)

    hendrix_server = service.MultiService()

    # Use django's WSGIHandler to create the resource.
    hendrix_resource = WSGIResource(reactor, threads, application)
    root = Root(hendrix_resource)
    if settings_module is not None:
        static_resource = MediaResource(settings_module.STATIC_ROOT)
        root.putChild(settings_module.STATIC_URL.strip('/'), static_resource)

    if additional_resources:
        for resource in additional_resources:
            root.putNamedChild(resource)

    main_site = server.Site(root)

    tcp_service = internet.TCPServer(port, main_site)
    threads_service = ThreadPoolService(threads)

    threads_service.setServiceParent(hendrix_server)
    tcp_service.setServiceParent(hendrix_server)


    return hendrix_resource, hendrix_server


class ThreadPoolService(service.Service):
    '''
    A simple class that defines a threadpool on init
    and provides for starting and stopping it.
    '''
    def __init__(self, pool):
        "self.pool returns the twisted.python.ThreadPool() instance."
        if not isinstance(pool, ThreadPool):
            msg = '%s must be initialised with a ThreadPool instance'
            raise TypeError(
                msg % self.__class__.__name__
            )
        self.pool = pool

    def startService(self):
        service.Service.startService(self)
        self.pool.start()

    def stopService(self):
        service.Service.stopService(self)
        self.pool.stop()


class HendrixResource(resource.Resource):
    """
    A wrapper that overrides the getChild method on Resource so to only serve
    the WSGIResource
    """

    def __init__(self, reactor, threads, application):
        resource.Resource.__init__(self)
        self.wsgi_resource = WSGIResource(reactor, threads, application)

    def getChild(self, name, request):
        """
        Postpath needs to contain all segments of
        the url, if it is incomplete then that incomplete url will be passed on
        to the child resource (in this case our wsgi application).
        """
        request.prepath = []
        request.postpath.insert(0, name)
        # re-establishes request.postpath so to contain the entire path
        return self.wsgi_resource

    def putNamedChild(self, resource):
        """
        putNamedChild takes either an instance of hendrix.contrib.NamedResource
        or any resource.Resource with a "namespace" attribute as a means of
        allowing application level control of resource namespacing.
        """
        try:
            path = resource.namespace
            self.putChild(path, resource)
        except AttributeError, e:
            msg = 'additional_resources instances must have a namespace attribute'
            raise AttributeError(msg), None, sys.exc_info()[2]


class MediaResource(static.File):
    '''
    A simple static service with directory listing disabled
    (gives the client a 403 instead of letting them browse
    a static directory).
    '''
    def directoryListing(self):
        # Override to forbid directory listing
        return resource.ForbiddenResource()
